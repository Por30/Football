"""Wall11 joint PPO/AMP with a train-only ball state prediction objective."""
import torch
from torch import nn
from torch.distributions import Normal
from rsl_rl.networks import MLP
from .carrybox import CarryBoxActorCritic
from .carrybox_wall10 import CarryBoxWall10PPO, CarryBoxWall10OnPolicyRunner
from perceptual_ball.kickball_v11 import CRITIC_DIM, FEATURE_SCHEMA, KickMotionLibrary, ball_state_loss


class KickballV11ActorCritic(CarryBoxActorCritic):
    def __init__(self, obs, obs_groups, num_actions, critic_hidden_dims=(512, 256, 256),
                 activation='elu', **kwargs):
        expected = {'policy': ['proprio', 'perception'], 'critic': ['critic_state']}
        if obs_groups != expected or obs['critic_state'].shape[-1] != CRITIC_DIM:
            raise ValueError('kickballv11 needs depth/proprio actor and critic124')
        if obs['proprio'].shape[-1] != 558 or tuple(obs['perception'].shape[1:]) != (4, 27, 48):
            raise ValueError('kickballv11 actor requires 6 proprio and 4 depth frames')
        super().__init__(obs, {'policy': ['proprio', 'perception'], 'critic': ['proprio', 'perception']},
                         num_actions, critic_hidden_dims=critic_hidden_dims, activation=activation, **kwargs)
        self.obs_groups = expected
        self.critic = MLP(CRITIC_DIM, 1, list(critic_hidden_dims), activation)
        self.pose_head = nn.Identity()
        self.ball_head = nn.Sequential(nn.Linear(558 + self.perception_encoder.output_dim, 128),
                                       nn.ELU(), nn.Linear(128, 6))

    def evaluate(self, obs, **kwargs):
        return self.critic(obs['critic_state'])

    def predict_ball(self, obs):
        return self.ball_head(self._features(obs))


class KickballV11PPO(CarryBoxWall10PPO):
    supports_auxiliary_objective = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.pose_aux_coef <= 0 or not torch.isfinite(torch.tensor(self.pose_aux_coef)):
            raise ValueError('kickballv11 needs a positive finite ball auxiliary coefficient')
        self.amp_config.update(schema=11, feature_schema=FEATURE_SCHEMA,
            auxiliary=dict(coef=self.pose_aux_coef, output='root_xyz_relative_inertial_velocity',
                           velocity_loss_scale=5., pairs='all_current_frames', actor_feedback=False))

    def _ensure_motion_library(self):
        if self.motion_library is None:
            library = KickMotionLibrary(self.amp_data_dir, self.device, 1 / self.control_dt)
            if self.motion_metadata is not None and self.motion_metadata != library.metadata:
                raise ValueError('kickballv11 AMP dataset/schema differs from checkpoint')
            self.motion_library, self.motion_metadata = library, library.metadata
        self.amp_statistics_initialized = True

    def _paired_training_outputs(self, current, mixed):
        latent = self.policy.perception_encoder(torch.cat((current['perception'], mixed['perception'])).float())
        features = torch.cat((torch.cat((current['proprio'], mixed['proprio'])).float(), latent), -1)
        mean, mixed_mean = self.policy.actor(features).chunk(2)
        self._ball_prediction = self.policy.ball_head(features[:len(mean)])
        value, mixed_value = self.policy.critic(torch.cat((current['critic_state'], mixed['critic_state']))).chunk(2)
        self.policy.distribution = Normal(mean, self.policy.log_std.exp().expand_as(mean))
        return value, mixed_mean, mixed_value

    def _auxiliary_loss(self, observations, indices):
        position, velocity = ball_state_loss(self._ball_prediction, observations['ball_target'][indices])
        self._aux_totals += len(indices) * torch.stack((position, velocity)).detach()
        self._aux_count += len(indices)
        return self.pose_aux_coef * (position + velocity)

    def update(self):
        self._aux_totals = torch.zeros(2, device=self.device)
        self._aux_count = 0
        result = super().update()
        position, velocity = (self._aux_totals / self._aux_count).tolist()
        self._ball_prediction = None
        result.update(ball_position=position, ball_velocity_scaled=velocity,
                      ball_aux_weighted=self.pose_aux_coef * (position + velocity))
        return result


class KickballV11OnPolicyRunner(CarryBoxWall10OnPolicyRunner):
    def _construct_algorithm(self, obs):
        if (self.policy_cfg.pop('class_name') != 'KickballV11ActorCritic'
                or self.alg_cfg.pop('class_name') != 'KickballV11PPO'):
            raise ValueError('Invalid kickballv11 learning classes')
        policy = KickballV11ActorCritic(obs, self.cfg['obs_groups'], self.env.num_actions,
                                       **self.policy_cfg).to(self.device)
        alg = KickballV11PPO(policy, device=self.device, multi_gpu_cfg=self.multi_gpu_cfg,
                             control_dt=self.env.unwrapped.step_dt, **self.alg_cfg)
        alg.init_storage('rl', self.env.num_envs, self.num_steps_per_env, obs, [self.env.num_actions])
        return alg

    def save(self, path, infos=None):
        super().save(path, infos)
        state = torch.load(path, map_location=self.device, weights_only=False)
        state['kickball_v11_schema'] = 1
        state['kickball_v11_curriculum'] = self.env.unwrapped._kickball.curriculum_state_dict()
        torch.save(state, path)

    def load(self, path, load_optimizer=True, map_location=None):
        state = torch.load(path, map_location=map_location or self.device, weights_only=False)
        if state.get('kickball_v11_schema') != 1:
            raise ValueError('Not a kickballv11 checkpoint')
        kb = self.env.unwrapped._kickball
        kb.validate_curriculum_state_dict(state.get('kickball_v11_curriculum'))
        result = super().load(path, load_optimizer, map_location)
        kb.curriculum_training = load_optimizer
        kb.load_curriculum_state_dict(state['kickball_v11_curriculum'])
        # Simulator caches can have been allocated by inference-mode rollouts.
        # The first resumed/play round must use the restored speed and gate.
        with torch.inference_mode():
            self.env.reset()
        return result

    def learn(self, *args, **kwargs):
        self.env.unwrapped._kickball.curriculum_training = True
        return super().learn(*args, **kwargs)
