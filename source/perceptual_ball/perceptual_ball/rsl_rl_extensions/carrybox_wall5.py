"""Wall5 stage-A AMP recipe. Reuses the unchanged visual PPO/auxiliary update."""
import torch
from rsl_rl.algorithms import PPO
from .amp import AMP
from .carrybox import CarryBoxActorCritic, CarryBoxPPO, CarryBoxOnPolicyRunner
from perceptual_ball.carrybox_amp import AMP_WINDOW
from perceptual_ball.carrybox_wall5 import WALL5_FRAME_DIM, WALL5_FEATURE_SCHEMA, Wall5MotionLibrary


class Wall5AMP(AMP):
    """Same initialization/LSGAN/0.5 gradient penalty, with raw 350D input.

    Inherited zero/one statistics buffers are retained for checkpoint auditing only;
    neither normalization nor the old +/-10 clipping participates in forward().
    """
    def forward(self, x):
        return self.amp_linear(self.trunk(x))

    def set_statistics(self, expert):
        raise RuntimeError('Wall5 uses raw features, not expert normalization')


class CarryBoxWall5PPO(CarryBoxPPO):
    def __init__(self, policy, *args, amp_reward_scale=.5, amp_lr=5.e-5, **kwargs):
        super().__init__(policy, *args, amp_reward_scale=amp_reward_scale, amp_lr=amp_lr, **kwargs)
        self.amp_config.update(
            schema=2, frame_dim=WALL5_FRAME_DIM, feature_schema=WALL5_FEATURE_SCHEMA,
            reward_time_scale='per_policy_step_no_dt', normalization='none', input_clip=None,
            reset_history='repeat_first_frame', valid_from_transition=1,
            discriminator_lr=amp_lr, weight_decay_trunk=1.e-3, weight_decay_output=.1,
            gradient_penalty=.5, max_grad_norm=10.,
            statistics_flag='raw_feature_pipeline_ready_no_fitted_statistics')
        if self.amp is not None:
            self.amp = Wall5AMP(AMP_WINDOW * WALL5_FRAME_DIM).to(self.device)
            self.amp_optimizer = torch.optim.Adam([
                {'params': self.amp.trunk.parameters(), 'weight_decay': 1.e-3},
                {'params': self.amp.amp_linear.parameters(), 'weight_decay': .1},
            ], lr=amp_lr)

    def init_storage(self, training_type, num_envs, num_transitions_per_env, obs, actions_shape):
        PPO.init_storage(self, training_type, num_envs, num_transitions_per_env, obs, actions_shape)
        if self.amp is not None:
            width = AMP_WINDOW * WALL5_FRAME_DIM
            if obs['amp'].shape != (num_envs, width):
                raise ValueError('Wall5 AMP requires 10 x 35 motion observations')
            self.amp_rollout = torch.zeros(num_transitions_per_env, num_envs, width, device=self.device)
            self.amp_valid = torch.zeros(num_transitions_per_env, num_envs, dtype=torch.bool, device=self.device)
            # Kept for the inherited checkpoint loader; no age-dependent masking.
            self.amp_age = torch.zeros(num_envs, dtype=torch.long, device=self.device)

    def _ensure_motion_library(self):
        if self.motion_library is None:
            library = Wall5MotionLibrary(self.amp_data_dir, device=self.device, env_fps=1. / self.control_dt)
            if self.motion_metadata is not None and self.motion_metadata != library.metadata:
                raise ValueError('Wall5 AMP resume dataset/schema differs from checkpoint')
            self.motion_library = library
            self.motion_metadata = library.metadata
        # This flag means the fixed raw-feature pipeline is ready, not fitted stats.
        self.amp_statistics_initialized = True

    def _process_amp(self, obs, rewards, dones, extras):
        self._ensure_motion_library()
        motion = obs['amp'].detach().clone()
        done = dones.bool().flatten()
        if done.any():
            terminal = extras.get('terminal_observations')
            if terminal is None or 'amp' not in terminal['obs']:
                raise RuntimeError('Wall5 AMP needs pre-reset terminal motion')
            ids = terminal['env_ids'].to(self.device)
            if not torch.equal(ids.sort().values, done.nonzero().flatten()):
                raise RuntimeError('Wall5 terminal environment IDs differ from done IDs')
            motion[ids] = terminal['obs']['amp'].to(self.device)
        if not torch.isfinite(motion).all():
            raise FloatingPointError('Non-finite Wall5 AMP motion')
        self.amp_rollout[self.storage.step].copy_(motion)
        self.amp_valid[self.storage.step].fill_(True)
        style = self.amp.predict_reward(motion)
        coef = self.amp_config['coef']
        task = (1. - coef) * rewards
        imitation = coef * self.amp_config['reward_scale'] * style
        mixed = task + imitation
        extras.setdefault('log', {}).update({
            'AMP/style_reward': style.mean().item(),
            'AMP/valid_fraction': 1.,
            'Reward/task_raw_per_step': rewards.mean().item(),
            'Reward/task_weighted_per_step': task.mean().item(),
            'Reward/amp_per_step': imitation.mean().item(),
            'Reward/mixed_per_step': mixed.mean().item(),
        })
        return mixed


class CarryBoxWall5OnPolicyRunner(CarryBoxOnPolicyRunner):
    def _construct_algorithm(self, obs):
        if (self.policy_cfg.pop('class_name') != 'CarryBoxActorCritic'
                or self.alg_cfg.pop('class_name') != 'CarryBoxWall5PPO'):
            raise ValueError('Invalid Wall5 learning classes')
        policy = CarryBoxActorCritic(obs, self.cfg['obs_groups'], self.env.num_actions, **self.policy_cfg).to(self.device)
        alg = CarryBoxWall5PPO(policy, device=self.device, multi_gpu_cfg=self.multi_gpu_cfg,
                              control_dt=self.env.unwrapped.step_dt, **self.alg_cfg)
        alg.init_storage('rl', self.env.num_envs, self.num_steps_per_env, obs, [self.env.num_actions])
        return alg
