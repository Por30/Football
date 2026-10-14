# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""AMP discriminator, ported from PhysHSI's `rsl_rl/rsl_rl/modules/amp.py` (same LSGAN-style loss
+ gradient-penalty formulation used across its G1 tasks). Kept as a plain `nn.Module` (not an
rsl_rl `PPO`/`ActorCritic` subclass) so `BallRegressionPPO` can own an instance and train it
alongside the ball-regression auxiliary head, mirroring how PhysHSI's `HIMPPO` owns its `AMP`.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from torch import autograd

DISC_LOGIT_INIT_SCALE = 1.0


class AMP(nn.Module):
    def __init__(self, num_obs: int, hidden_dims: tuple[int, ...] = (512, 256)):
        super().__init__()
        layers = []
        dim_in = num_obs
        for dim_out in hidden_dims:
            layer = nn.Linear(dim_in, dim_out)
            nn.init.kaiming_uniform_(layer.weight, nonlinearity="relu")
            nn.init.zeros_(layer.bias)
            layers += [layer, nn.ReLU()]
            dim_in = dim_out
        self.trunk = nn.Sequential(*layers)
        self.amp_linear = nn.Linear(dim_in, 1)
        nn.init.uniform_(self.amp_linear.weight, -0.01, 0.01)
        nn.init.zeros_(self.amp_linear.bias)
        self.register_buffer("obs_mean", torch.zeros(num_obs))
        self.register_buffer("obs_std", torch.ones(num_obs))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.amp_linear(self.trunk(((x - self.obs_mean) / self.obs_std).clamp(-10, 10)))

    @torch.no_grad()
    def set_statistics(self, expert):
        self.obs_mean.copy_(expert.mean(0))
        self.obs_std.copy_(expert.std(0).clamp(min=0.1))

    def compute_grad_pen(self, expert_state: torch.Tensor, lambda_: float = 5.0) -> torch.Tensor:
        expert_state = expert_state.clone().requires_grad_(True)
        logit = self.forward(expert_state)
        grad = autograd.grad(
            outputs=logit,
            inputs=expert_state,
            grad_outputs=torch.ones_like(logit),
            create_graph=True,
            retain_graph=True,
            only_inputs=True,
        )[0]
        return lambda_ * (grad.pow(2).sum(dim=-1)).mean()

    def compute_loss(self, policy_obs: torch.Tensor, expert_obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        policy_d = self.forward(policy_obs)
        expert_d = self.forward(expert_obs)
        expert_loss = (expert_d - 1).pow(2).mean()
        policy_loss = (policy_d + 1).pow(2).mean()
        gail_loss = expert_loss + policy_loss
        grad_pen = self.compute_grad_pen(expert_obs) * 0.1
        return gail_loss + grad_pen, expert_loss, policy_loss

    def predict_reward(self, obs: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            d = self.forward(obs)
            reward = torch.clamp(1.0 - 0.25 * (d - 1.0).pow(2), min=0.0)
        return reward.squeeze(-1)


class SkillAMP(nn.Module):
    """One independent AMP discriminator per skill, as in the v11 recipe (`discriminator count:
    2`, each `600 -> 512 -> 256 -> 1`).

    A single discriminator over both kick clips only ever answers "does this look like *a* kick",
    which carries no information about which foot is being used: a left-footed swing scores just
    as well while the robot is routed to the right-foot skill, so the style reward cannot teach
    the two apart and the policy is free to collapse onto one favourite foot. With a
    discriminator per clip, the skill the env routes to (from the ball's lateral position, see
    `mdp.kickball_state`) picks the one that grades the motion, and the style reward only pays
    for a swing that matches the side the ball is actually on.

    Kept as fully separate networks rather than a shared trunk with two heads, matching the
    recipe: the two clips are near mirror images, and a shared trunk would have to represent both
    at once in the same features, which is exactly the entanglement this is meant to avoid.
    """

    def __init__(self, num_obs: int, num_skills: int = 2, hidden_dims: tuple[int, ...] = (512, 256)):
        super().__init__()
        self.num_skills = num_skills
        self.discriminators = nn.ModuleList([AMP(num_obs, hidden_dims) for _ in range(num_skills)])

    def set_statistics(self, expert):
        for disc in self.discriminators:
            disc.set_statistics(expert)

    def trunk_parameters(self):
        return [p for disc in self.discriminators for p in disc.trunk.parameters()]

    def head_parameters(self):
        return [p for disc in self.discriminators for p in disc.amp_linear.parameters()]

    def predict_reward(self, obs: torch.Tensor, skill_ids: torch.Tensor) -> torch.Tensor:
        """Style reward from each env's own routed discriminator.

        Evaluated per skill on that skill's rows only, so a discriminator never sees -- or costs
        anything for -- transitions that were not routed to it.
        """
        reward = torch.zeros(obs.shape[0], device=obs.device)
        for skill, disc in enumerate(self.discriminators):
            rows = skill_ids == skill
            if rows.any():
                reward[rows] = disc.predict_reward(obs[rows])
        return reward

    def compute_skill_loss(self, policy_obs: torch.Tensor, expert_obs: torch.Tensor, skill: int):
        return self.discriminators[skill].compute_loss(policy_obs, expert_obs)
