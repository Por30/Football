"""Wall5 task AMP, running normalization, visibility-masked pose and adaptive PPO."""
import torch
from rsl_rl.networks import MLP
from rsl_rl.algorithms import PPO
from .amp import AMP
from .carrybox import CarryBoxActorCritic, CarryBoxPPO, CarryBoxOnPolicyRunner, box_pose_loss
from perceptual_ball.carrybox_amp import AMP_WINDOW
from perceptual_ball.carrybox_wall5 import WALL5_FRAME_DIM, WALL5_FEATURE_SCHEMA, Wall5MotionLibrary


class CarryBoxWall5ActorCritic(CarryBoxActorCritic):
    """Depth/proprio actor with a separate training-only privileged value MLP."""
    def __init__(self, obs, obs_groups, num_actions, critic_hidden_dims=(512, 256, 256),
                 activation='elu', **kwargs):
        expected = {'policy': ['proprio', 'perception'], 'critic': ['critic_state']}
        if obs_groups != expected or obs['critic_state'].ndim != 2 or obs['critic_state'].shape[-1] != 108:
            raise ValueError('Wall5 requires depth/proprio actor and independent critic_state108')
        # Reuse the unchanged actor/encoder/pose initialization and export interface.
        super().__init__(obs, {'policy': ['proprio', 'perception'], 'critic': ['proprio', 'perception']},
                         num_actions, critic_hidden_dims=critic_hidden_dims, activation=activation, **kwargs)
        self.obs_groups = expected
        self.critic = MLP(108, 1, list(critic_hidden_dims), activation)

    def evaluate(self, obs, **kwargs):
        return self.critic(obs['critic_state'])


def visible_box_pose_loss(prediction, target):
    if target.shape[-1] != 10:
        raise ValueError('Wall5 pose supervision requires xyz/rotation6/paired visibility')
    valid = target[:, 9] > .5
    if not valid.any():
        zero = prediction.sum() * 0.
        return zero, zero
    return box_pose_loss(prediction[valid], target[valid, :9])


class Wall5AMP(AMP):
    """Running raw-frame statistics, shared across 10 time slots, clip +/-10.

    Initialized with experts; updated once before each discriminator update from
    equal-size raw expert/policy samples. Frozen during reward and minibatches.
    Gradient penalty acts on normalized input coordinates (coefficient 0.5).
    """
    def __init__(self, num_obs):
        super().__init__(num_obs)
        self.register_buffer('running_var', torch.ones(WALL5_FRAME_DIM))
        self.register_buffer('running_count', torch.zeros((), dtype=torch.float64))

    @torch.no_grad()
    def update_statistics(self, raw):
        frames = raw.reshape(-1, WALL5_FRAME_DIM)
        if not len(frames):
            return
        if not torch.isfinite(frames).all():
            raise FloatingPointError('Non-finite raw AMP statistics')
        mean = frames.mean(0)
        variance = frames.var(0, unbiased=False)
        n = len(frames)
        total = self.running_count + n
        delta = mean - self.obs_mean[:WALL5_FRAME_DIM]
        ratio = (n / total).float()
        merged_mean = self.obs_mean[:WALL5_FRAME_DIM] + delta * ratio
        merged_var = self.running_var * (1-ratio) + variance * ratio + delta.square() * (1-ratio) * ratio
        self.running_var.copy_(merged_var.clamp_min(0))
        self.running_count.copy_(total)
        self.obs_mean.copy_(merged_mean.repeat(AMP_WINDOW))
        self.obs_std.copy_(torch.sqrt(self.running_var + 1.e-4).repeat(AMP_WINDOW))

    def set_statistics(self, expert):
        if self.running_count > 0:
            raise RuntimeError('Do not refit restored AMP normalization')
        self.update_statistics(expert)

    def normalized(self, raw):
        return ((raw-self.obs_mean)/self.obs_std).clamp(-10., 10.)

    def compute_loss(self, policy_obs, expert_obs):
        policy = self.normalized(policy_obs).detach()
        expert = self.normalized(expert_obs).detach().requires_grad_(True)
        policy_d = self.amp_linear(self.trunk(policy))
        expert_d = self.amp_linear(self.trunk(expert))
        expert_loss = (expert_d-1).square().mean()
        policy_loss = (policy_d+1).square().mean()
        gradient = torch.autograd.grad(expert_d, expert, torch.ones_like(expert_d), create_graph=True)[0]
        return expert_loss + policy_loss + .5*gradient.square().sum(-1).mean(), expert_loss, policy_loss


class CarryBoxWall5PPO(CarryBoxPPO):
    supported_schedules = ('fixed', 'adaptive')
    def __init__(self, policy, *args, amp_reward_scale=.5, amp_lr=5.e-5, **kwargs):
        super().__init__(policy, *args, amp_reward_scale=amp_reward_scale, amp_lr=amp_lr, **kwargs)
        self.amp_config.update(
            schema=3, frame_dim=WALL5_FRAME_DIM, feature_schema=WALL5_FEATURE_SCHEMA,
            reward_time_scale='per_policy_step_no_dt', normalization='running_raw_frame60_shared_time', input_clip=10., normalization_epsilon=1.e-4,
            reset_history='repeat_first_frame', valid_from_transition=1,
            discriminator_lr=amp_lr, weight_decay_trunk=1.e-3, weight_decay_output=.1,
            gradient_penalty=.5, max_grad_norm=10.,
            statistics_flag='running_mean_variance_count_checkpointed',
            normalization_update='equal_expert_policy_before_discriminator_once',
            gradient_penalty_coordinates='normalized', pose_target='visible_paired_xyz_rot6_mask',
            ppo=dict(schedule=self.schedule, desired_kl=self.desired_kl, initial_lr=self.learning_rate,
                     entropy=self.entropy_coef, epochs=self.num_learning_epochs, mini_batches=self.num_mini_batches))
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
                raise ValueError('Wall5 AMP requires 10 x 60 motion observations')
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
        if not self.amp_statistics_initialized:
            self.amp.set_statistics(self.motion_library.sample_expert_amp_obs(2048))
            self.amp_statistics_initialized = True

    def _training_outputs(self, obs):
        # Reuse one CNN pass for the actor and auxiliary head. The asymmetric
        # value loss only reaches its independent MLP, never the depth encoder.
        policy = self.policy
        latent = policy.perception_encoder(obs['perception'])
        features = torch.cat((obs['proprio'], latent), -1)
        mean = policy.actor(features)
        policy.distribution = torch.distributions.Normal(mean, policy.log_std.exp().expand_as(mean))
        policy.distribution.sample()  # preserve the former act() RNG consumption
        critic_features = obs['critic_state'] if isinstance(policy, CarryBoxWall5ActorCritic) else features
        return policy.critic(critic_features), policy.pose_head(latent)

    def _pose_loss(self, prediction, target):
        return visible_box_pose_loss(prediction, target)

    @torch.no_grad()
    def _adapt_learning_rate(self, old_mu, old_sigma):
        if self.schedule != 'adaptive' or self.desired_kl is None:
            return
        mu, sigma = self.policy.action_mean, self.policy.action_std
        kl = torch.sum(torch.log(sigma/old_sigma + 1.e-5) +
                       (old_sigma.square()+(old_mu-mu).square())/(2*sigma.square())-.5, dim=-1).mean()
        if not torch.isfinite(kl):
            raise FloatingPointError('Non-finite Wall5 KL')
        self.last_kl = kl.item()
        if kl > self.desired_kl*2:
            self.learning_rate = max(1.e-5, self.learning_rate/1.5)
        elif 0 < kl < self.desired_kl/2:
            self.learning_rate = min(1.e-2, self.learning_rate*1.5)
        for group in self.optimizer.param_groups:
            group['lr'] = self.learning_rate

    def update(self):
        targets = self.storage.observations['box_pose_target']
        valid = targets[..., 9] > .5
        visible_fraction = valid.float().mean().item()
        visible_distance = targets[..., :3][valid].norm(dim=-1).mean().item() if valid.any() else 0.
        result = super().update()
        result.update(box_visible_fraction=visible_fraction, box_visible_distance=visible_distance,
                      ppo_kl=getattr(self, 'last_kl', 0.), ppo_learning_rate=self.learning_rate)
        return result

    def _update_amp(self):
        policy_motion = self.amp_rollout[self.amp_valid].detach()
        if len(policy_motion):
            # Bound the normalization cost at large rollout sizes, sample both distributions equally.
            ids = torch.randperm(len(policy_motion), device=self.device)[:2048]
            expert = self.motion_library.sample_expert_amp_obs(len(ids))
            self.amp.update_statistics(torch.cat((policy_motion[ids], expert)))
        result = super()._update_amp()
        result['amp_normalizer_count'] = self.amp.running_count.item()
        result['amp_normalizer_min_std'] = self.amp.obs_std.min().item()
        return result

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
    def load(self, path, load_optimizer=True, map_location=None):
        result = super().load(path, load_optimizer, map_location)
        if load_optimizer:
            self.alg.learning_rate = self.alg.optimizer.param_groups[0]['lr']
        return result

    def _construct_algorithm(self, obs):
        if (self.policy_cfg.pop('class_name') != 'CarryBoxWall5ActorCritic'
                or self.alg_cfg.pop('class_name') != 'CarryBoxWall5PPO'):
            raise ValueError('Invalid Wall5 learning classes')
        policy = CarryBoxWall5ActorCritic(obs, self.cfg['obs_groups'], self.env.num_actions, **self.policy_cfg).to(self.device)
        alg = CarryBoxWall5PPO(policy, device=self.device, multi_gpu_cfg=self.multi_gpu_cfg,
                              control_dt=self.env.unwrapped.step_dt, **self.alg_cfg)
        alg.init_storage('rl', self.env.num_envs, self.num_steps_per_env, obs, [self.env.num_actions])
        return alg
