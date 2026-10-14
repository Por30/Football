# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch
import torch.nn as nn
from torch.distributions import Normal

from rsl_rl.modules import ActorCritic
from rsl_rl.networks import MLP, EmpiricalNormalization


_ACTIVATIONS = {"elu": nn.ELU, "relu": nn.ReLU}


class DepthCNNEncoder(nn.Module):
    """Conv stack over the depth history, optionally with a frame-difference channel.

    The `num_frames` history frames go in as CNN channels. With `use_frame_diff` (the v11
    `DepthActorFrameDiff` behaviour) one extra channel carries `depth[-1] - depth[-2]`: a stack
    of still frames already contains that difference, but only implicitly, spread across two
    channels the first convolution has to subtract for itself, and handing it over directly puts
    ball motion -- the one thing in this image that moves -- in the very first layer.

    Either way the spatial path is 27x48 -> 14x24 -> 7x12 -> 4x6 -> (maxpool) 2x3, so the
    flattened feature is 64*2*3 = 384.

    The defaults reproduce the v3 task's encoder exactly, so `Template-Perceptual-Ball-v0`
    checkpoints keep loading; soccer-v2 passes the v11 settings (5x5 first kernel, ReLU, frame
    difference) from its agent config.
    """

    def __init__(
        self,
        num_frames: int,
        height: int,
        width: int,
        conv_channels: tuple[int, ...] = (16, 32, 64),
        conv_kernels: tuple[int, ...] = (3, 3, 3),
        conv_strides: tuple[int, ...] = (2, 2, 2),
        conv_paddings: tuple[int, ...] = (1, 1, 1),
        head_dim: int = 256,
        latent_dim: int = 128,
        activation: str = "elu",
        use_frame_diff: bool = False,
    ):
        super().__init__()
        self.num_frames = num_frames
        self.use_frame_diff = use_frame_diff
        act_cls = _ACTIVATIONS[activation]

        layers: list[nn.Module] = []
        c_in = num_frames + (1 if use_frame_diff else 0)
        for c_out, kernel, stride, padding in zip(conv_channels, conv_kernels, conv_strides, conv_paddings):
            layers += [nn.Conv2d(c_in, c_out, kernel_size=kernel, stride=stride, padding=padding), act_cls()]
            c_in = c_out
        layers.append(nn.MaxPool2d(kernel_size=2))
        self.conv = nn.Sequential(*layers)

        with torch.no_grad():
            num_in_channels = num_frames + (1 if use_frame_diff else 0)
            flat_dim = self.conv(torch.zeros(1, num_in_channels, height, width)).numel()
        self.head = nn.Sequential(
            nn.Flatten(), nn.Linear(flat_dim, head_dim), act_cls(), nn.Linear(head_dim, latent_dim)
        )
        self.output_dim = latent_dim

    def forward(self, depth: torch.Tensor) -> torch.Tensor:
        if self.use_frame_diff:
            depth = torch.cat([depth, depth[:, -1:] - depth[:, -2:-1]], dim=1)
        return self.head(self.conv(depth))


class PerceptionActorCritic(ActorCritic):
    """Actor-critic whose depth-camera ("perception") input -- a (N, num_frames, H, W) stack of
    synthetic depth frames, see mdp/perception.py -- goes through a CNN encoder that is also
    trained to regress the ball's true position/velocity (the "privileged" obs group, see
    `BallRegressionPPO`). Task reward alone gives a very weak gradient for "extract the ball from
    this depth image", so this auxiliary regression target is what actually pushes the encoder --
    and therefore the actor, which consumes its output -- to represent the ball's location
    instead of ignoring the camera.

    With `num_critics > 1` the class holds that many independent critics, one per skill, and
    `evaluate` returns the value of whichever one the env's current skill gating selects. Keeping
    the selection inside `evaluate` is what makes the rest of PPO -- GAE, the timeout bootstrap,
    the value loss -- use that same gating without any of them having to know about skills: the
    unselected critic is multiplied by zero, so it receives no gradient from a transition that
    was not routed to it.

    The critic does not see "perception" at all (matching the recipe): it's a plain MLP over
    whatever flat obs groups `obs_groups["critic"]` lists (proprio + the robot's own velocity +
    the privileged ball state), so the base `ActorCritic`'s machinery is reused unchanged for it.
    Because "perception" is image-shaped rather than a flat vector, this class does not call
    `ActorCritic.__init__` (its dimension bookkeeping assumes every obs group is 2D) and instead
    duplicates the small parts of it that still apply.
    """

    def __init__(
        self,
        obs,
        obs_groups,
        num_actions,
        perception_group: str = "perception",
        privileged_group: str = "privileged",
        skill_group: str = "skill",
        actor_hidden_dims: tuple[int, ...] = (512, 256, 256),
        critic_hidden_dims: tuple[int, ...] = (512, 256, 256),
        activation: str = "elu",
        init_noise_std: float = 1.0,
        noise_std_type: str = "scalar",
        actor_obs_normalization: bool = False,  # noqa: ARG002 -- accepted, always bypassed (see below)
        critic_obs_normalization: bool = True,
        num_critics: int = 1,
        depth_conv_kernels: tuple[int, ...] = (3, 3, 3),
        depth_conv_paddings: tuple[int, ...] = (1, 1, 1),
        depth_activation: str = "elu",
        depth_use_frame_diff: bool = False,
        ball_head_hidden_dim: int | None = None,
        ball_aux_fuse_proprio: bool = False,
        **kwargs,
    ):
        nn.Module.__init__(self)
        if kwargs:
            print(f"PerceptionActorCritic.__init__ got unexpected arguments, which will be ignored: {list(kwargs)}")

        self.obs_groups = obs_groups
        self.perception_group = perception_group
        self.privileged_group = privileged_group
        self.skill_group = skill_group
        self.num_critics = num_critics
        self.ball_aux_fuse_proprio = ball_aux_fuse_proprio

        # critics: plain flat-vector MLPs, exactly like the base ActorCritic's single one. With
        # one critic the module keeps the base class's `critic` attribute name, so checkpoints
        # trained on the single-critic v3 task still load into this class unchanged.
        num_critic_obs = sum(obs[group].shape[-1] for group in obs_groups["critic"])
        if num_critics == 1:
            self.critic = MLP(num_critic_obs, 1, list(critic_hidden_dims), activation)
        else:
            self.critics = nn.ModuleList(
                [MLP(num_critic_obs, 1, list(critic_hidden_dims), activation) for _ in range(num_critics)]
            )
        self.critic_obs_normalization = critic_obs_normalization
        self.critic_obs_normalizer = EmpiricalNormalization(num_critic_obs) if critic_obs_normalization else nn.Identity()

        # actor: proprio (flat) concatenated with the CNN-encoded perception latent
        num_frames, height, width = obs[perception_group].shape[1:]
        num_ball_state = obs[privileged_group].shape[-1]
        num_other_actor_obs = sum(
            obs[group].shape[-1] for group in obs_groups["policy"] if group != perception_group
        )
        self.perception_encoder = DepthCNNEncoder(
            num_frames,
            height,
            width,
            conv_kernels=tuple(depth_conv_kernels),
            conv_paddings=tuple(depth_conv_paddings),
            activation=depth_activation,
            use_frame_diff=depth_use_frame_diff,
        )
        latent_dim = self.perception_encoder.output_dim
        aux_dim = latent_dim + (num_other_actor_obs if ball_aux_fuse_proprio else 0)
        # a bare linear probe by default (the v3 task); `ball_head_hidden_dim=128` gives the v11
        # recipe's 128 -> 128 -> 6 head
        if ball_head_hidden_dim is None:
            self.ball_head = nn.Linear(aux_dim, num_ball_state)
        else:
            self.ball_head = nn.Sequential(
                nn.Linear(aux_dim, ball_head_hidden_dim),
                nn.ReLU(),
                nn.Linear(ball_head_hidden_dim, num_ball_state),
            )
        self.actor = MLP(num_other_actor_obs + self.perception_encoder.output_dim, num_actions, list(actor_hidden_dims), activation)
        # the actor bypasses obs normalization entirely -- it routes "perception" through its own
        # CNN encoder instead of a flat normalized vector, so there is nothing for this to do
        self.actor_obs_normalization = False
        self.actor_obs_normalizer = nn.Identity()
        print(f"Perception encoder: {self.perception_encoder}")
        print(f"Ball regression head: {self.ball_head}")
        print(f"Actor MLP (perception-encoded): {self.actor}")
        print(f"Critic MLP (x{num_critics}): {self.critic if num_critics == 1 else self.critics[0]}")

        self.noise_std_type = noise_std_type
        if noise_std_type == "scalar":
            self.std = nn.Parameter(init_noise_std * torch.ones(num_actions))
        elif noise_std_type == "log":
            self.log_std = nn.Parameter(torch.log(init_noise_std * torch.ones(num_actions)))
        else:
            raise ValueError(f"Unknown standard deviation type: {noise_std_type}. Should be 'scalar' or 'log'")

        self.distribution = None
        Normal.set_default_validate_args(False)

    def _actor_features(self, obs) -> torch.Tensor:
        feats = [
            self.perception_encoder(obs[group]) if group == self.perception_group else obs[group]
            for group in self.obs_groups["policy"]
        ]
        return torch.cat(feats, dim=-1)

    def update_distribution(self, obs) -> None:
        mean = self.actor(self._actor_features(obs))
        if self.noise_std_type == "scalar":
            std = self.std.expand_as(mean)
        elif self.noise_std_type == "log":
            std = torch.exp(self.log_std).expand_as(mean)
        else:
            raise ValueError(f"Unknown standard deviation type: {self.noise_std_type}. Should be 'scalar' or 'log'")
        self.distribution = Normal(mean, std)

    def act(self, obs, **kwargs) -> torch.Tensor:
        self.update_distribution(obs)
        return self.distribution.sample()

    def act_inference(self, obs) -> torch.Tensor:
        return self.actor(self._actor_features(obs))

    def evaluate(self, obs, **kwargs) -> torch.Tensor:
        """The skill-selected value, as a single column (see the class docstring)."""
        critic_obs = self.critic_obs_normalizer(self.get_critic_obs(obs))
        if self.num_critics == 1:
            return self.critic(critic_obs)
        values = torch.cat([critic(critic_obs) for critic in self.critics], dim=-1)
        return (values * obs[self.skill_group]).sum(dim=-1, keepdim=True)

    def predict_ball_state(self, obs) -> torch.Tensor:
        """Regress the ball's privileged state from the perception encoder (the auxiliary task)."""
        features = self._actor_features(obs) if self.ball_aux_fuse_proprio else self.perception_encoder(obs[self.perception_group])
        return self.ball_head(features)
