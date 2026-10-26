"""Wall11 joint PPO/AMP with size-aware, training-only depth pose regression."""
import math
import torch
from torch.distributions import Normal
from perceptual_ball.carrybox_wall12 import POSE_CONTRACT, box_pose_loss
from .carrybox_wall10 import CarryBoxWall10ActorCritic, CarryBoxWall10PPO, CarryBoxWall10OnPolicyRunner


class CarryBoxWall12PPO(CarryBoxWall10PPO):
    supports_auxiliary_objective = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not math.isfinite(self.pose_aux_coef) or self.pose_aux_coef <= 0:
            raise ValueError('Wall12 requires a positive finite pose auxiliary coefficient')
        # Parent freezes and excludes this compatibility head. Keep the SAME
        # three Adam groups and AMP alias while enabling its training here.
        head = list(self.policy.pose_head.parameters())
        for parameter in head:
            parameter.requires_grad_(True)
        self.optimizer.param_groups[0]['params'].extend(head)
        self.amp_config.update(schema=12, auxiliary=dict(POSE_CONTRACT, coef=self.pose_aux_coef))

    def init_storage(self, training_type, num_envs, num_transitions_per_env, obs, actions_shape):
        if obs['box_pose_target'].shape != (num_envs, 12):
            raise ValueError('Wall12 requires paired xyz/rot6/size labels with 12 columns')
        super().init_storage(training_type, num_envs, num_transitions_per_env, obs, actions_shape)

    def _paired_training_outputs(self, current, mixed):
        latent = self.policy.perception_encoder(torch.cat((current['perception'], mixed['perception'])).float())
        proprio = torch.cat((current['proprio'], mixed['proprio'])).float()
        mean, mixed_mean = self.policy.actor(torch.cat((proprio, latent), -1)).chunk(2)
        self._pose_prediction = self.policy.pose_head(latent[:len(mean)])
        value, mixed_value = self.policy.critic(torch.cat((current['critic_state'], mixed['critic_state']))).chunk(2)
        self.policy.distribution = Normal(mean, self.policy.log_std.exp().expand_as(mean))
        return value, mixed_mean, mixed_value

    def _auxiliary_loss(self, observations, indices):
        position, rotation = box_pose_loss(self._pose_prediction, observations['box_pose_target'][indices])
        self._pose_prediction = None
        self._pose_totals += len(indices) * torch.stack((position, rotation)).detach()
        self._pose_count += len(indices)
        return self.pose_aux_coef * (position + rotation)

    def update(self):
        self._pose_totals = torch.zeros(2, device=self.device)
        self._pose_count = 0
        try:
            result = super().update()
        finally:
            self._pose_prediction = None
        position, rotation = (self._pose_totals / self._pose_count).tolist()
        result.update(pose_position=position, pose_rotation=rotation,
                      pose_aux_weighted=self.pose_aux_coef * (position + rotation),
                      pose_samples=float(self._pose_count))
        return result


class CarryBoxWall12OnPolicyRunner(CarryBoxWall10OnPolicyRunner):
    def _construct_algorithm(self, obs):
        if (self.policy_cfg.pop('class_name') != 'CarryBoxWall10ActorCritic'
                or self.alg_cfg.pop('class_name') != 'CarryBoxWall12PPO'):
            raise ValueError('Invalid wall12 learning classes')
        policy = CarryBoxWall10ActorCritic(obs, self.cfg['obs_groups'], self.env.num_actions,
                                          **self.policy_cfg).to(self.device)
        alg = CarryBoxWall12PPO(policy, device=self.device, multi_gpu_cfg=self.multi_gpu_cfg,
                               control_dt=self.env.unwrapped.step_dt, **self.alg_cfg)
        alg.init_storage('rl', self.env.num_envs, self.num_steps_per_env, obs, [self.env.num_actions])
        return alg
