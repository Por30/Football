"""Explicit box-pose feedback for wall13; inherit wall12 supervision and optimizer."""
import torch
from torch import nn
from torch.distributions import Normal
from perceptual_ball.carrybox_wall13 import POSE_FEEDBACK_CONTRACT, VISUAL_FEEDBACK_CONTRACT
from .carrybox_wall10 import CarryBoxWall10ActorCritic
from .carrybox_wall12 import CarryBoxWall12PPO, CarryBoxWall12OnPolicyRunner


class CarryBoxWall13ActorCritic(CarryBoxWall10ActorCritic):
    uses_box_pose_feedback = True
    box_pose_feedback_contract = VISUAL_FEEDBACK_CONTRACT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.perception_encoder.output_dim != 128:
            raise ValueError('Wall13 requires 128-D depth features')
        first = self.actor[0]
        self.actor[0] = nn.Linear(first.in_features + 9, first.out_features)
        # Keep the export interface; direct concatenation has no fusion weights.
        self.box_pose_fusion = nn.Identity()

    def fuse_depth_features(self, latent, prediction):
        return self.box_pose_fusion(torch.cat((latent, prediction), -1))

    def _features(self, obs):
        latent = self.perception_encoder(obs['perception'].float())
        prediction = self.pose_head(latent)
        fused = self.fuse_depth_features(latent, prediction)
        return torch.cat((obs['proprio'].float(), fused), -1)


class CarryBoxWall13PPO(CarryBoxWall12PPO):
    def __init__(self, policy, *args, **kwargs):
        if not isinstance(policy, CarryBoxWall13ActorCritic):
            raise ValueError('Wall13 PPO requires the pose-feedback actor')
        # Parent includes the 695-input actor in Adam, then unfreezes/adds
        # the pose head exactly once. Keep its three joint optimizer groups.
        super().__init__(policy, *args, **kwargs)
        self.amp_config.update(schema=13,
            auxiliary=dict(POSE_FEEDBACK_CONTRACT, coef=self.pose_aux_coef),
            visual_feedback=dict(VISUAL_FEEDBACK_CONTRACT))

    def _paired_training_outputs(self, current, mixed):
        latent = self.policy.perception_encoder(torch.cat((current['perception'], mixed['perception'])).float())
        prediction = self.policy.pose_head(latent)
        fused = self.policy.fuse_depth_features(latent, prediction)
        proprio = torch.cat((current['proprio'], mixed['proprio'])).float()
        mean, mixed_mean = self.policy.actor(torch.cat((proprio, fused), -1)).chunk(2)
        self._pose_prediction = prediction[:len(mean)]
        value, mixed_value = self.policy.critic(torch.cat((current['critic_state'], mixed['critic_state']))).chunk(2)
        self.policy.distribution = Normal(mean, self.policy.log_std.exp().expand_as(mean))
        return value, mixed_mean, mixed_value


class CarryBoxWall13OnPolicyRunner(CarryBoxWall12OnPolicyRunner):
    def _construct_algorithm(self, obs):
        if (self.policy_cfg.pop('class_name') != 'CarryBoxWall13ActorCritic'
                or self.alg_cfg.pop('class_name') != 'CarryBoxWall13PPO'):
            raise ValueError('Invalid wall13 learning classes')
        policy = CarryBoxWall13ActorCritic(obs, self.cfg['obs_groups'], self.env.num_actions,
                                         **self.policy_cfg).to(self.device)
        alg = CarryBoxWall13PPO(policy, device=self.device, multi_gpu_cfg=self.multi_gpu_cfg,
                               control_dt=self.env.unwrapped.step_dt, **self.alg_cfg)
        alg.init_storage('rl', self.env.num_envs, self.num_steps_per_env, obs, [self.env.num_actions])
        return alg
