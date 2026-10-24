"""PhysHSI joint PPO/AMP optimizer and temporal smoothness, adapted to depth."""
import torch
from torch import nn
from torch.distributions import Normal
from .amp import AMP
from .carrybox import CarryBoxPPO, CarryBoxOnPolicyRunner
from .carrybox_wall5 import CarryBoxWall5ActorCritic, CarryBoxWall5PPO
from perceptual_ball.carrybox_wall10 import Wall10MotionLibrary, FEATURE_SCHEMA


class CarryBoxWall10ActorCritic(CarryBoxWall5ActorCritic):
    def _features(self, obs):
        return torch.cat((obs['proprio'].float(), self.perception_encoder(obs['perception'].float())), -1)


class PhysHSIAMP(AMP):
    def __init__(self):
        nn.Module.__init__(self)
        self.trunk = nn.Sequential(nn.Linear(600, 512), nn.ReLU(), nn.Linear(512, 256), nn.ReLU())
        self.amp_linear = nn.Linear(256, 1)
        for layer in (self.trunk[2], self.amp_linear):
            nn.init.uniform_(layer.weight, -1., 1.)
            nn.init.zeros_(layer.bias)

    def forward(self, obs):
        return self.amp_linear(self.trunk(obs))


class CarryBoxWall10PPO(CarryBoxWall5PPO):
    # The checkpoint's cnn_microbatch=256 remains the logical random block.
    # Only deterministic tensor work is merged; every original draw is retained.
    cnn_execution_batch_size = 8192

    def __init__(self, policy, *args, **kwargs):
        # Deliberately bypass wall5's Normalizer, separate Adam and mean/std penalties.
        CarryBoxPPO.__init__(self, policy, *args, **kwargs)
        if self.amp is None or self.pose_aux_coef != 0:
            raise ValueError('Wall10 requires AMP and the source zero auxiliary coefficient')
        self.amp = PhysHSIAMP().to(self.device)
        for parameter in policy.pose_head.parameters():
            parameter.requires_grad_(False)
        self.optimizer = torch.optim.Adam([
            {'params': [p for p in policy.parameters() if p.requires_grad], 'weight_decay': 0.},
            {'params': self.amp.trunk.parameters(), 'weight_decay': .001},
            {'params': self.amp.amp_linear.parameters(), 'weight_decay': .1}], lr=self.learning_rate)
        # The schema2 serializer stores both names; they intentionally alias the
        # SAME optimizer and resume restores that same combined state.
        self.amp_optimizer = self.optimizer
        self.amp_config = dict(schema=10, coef=.25, reward_scale=.5, frame_dim=60,
            feature_schema=FEATURE_SCHEMA, window_length=10, normalization='none',
            reward_time_scale='per_step_no_dt', optimizer='joint_adam_ac_amp',
            weight_decay=[0., .001, .1], gradient_penalty=.5,
            policy_smooth_coef=1/9, value_smooth_coef=1/90,
            temporal_samples='first_Tminus1_continuation_1minusdone',
            reset_history='repeat_current_frame_no_cross_episode_history',
            cnn_microbatch=256, depth_rollout_dtype='float32',
            ppo=dict(initial_lr=self.learning_rate, schedule=self.schedule, desired_kl=self.desired_kl,
                     epochs=self.num_learning_epochs, minibatches=self.num_mini_batches,
                     entropy=self.entropy_coef, gamma=self.gamma, lam=self.lam,
                     clip=self.clip_param, max_grad_norm=self.max_grad_norm))
        if kwargs.get('amp_coef', .25) != .25 or kwargs.get('amp_reward_scale', .5) != .5:
            raise ValueError('Wall10 requires source reward mixture .75 task + .125 style')

    def _ensure_motion_library(self):
        if self.motion_library is None:
            library = Wall10MotionLibrary(self.amp_data_dir, device=self.device, env_fps=1/self.control_dt)
            if self.motion_metadata is not None and library.metadata != self.motion_metadata:
                raise ValueError('Wall10 AMP dataset/schema differs from checkpoint')
            self.motion_library, self.motion_metadata = library, library.metadata
        self.amp_statistics_initialized = True  # Identity/no statistics is explicit in the contract.

    def init_storage(self, training_type, num_envs, num_transitions_per_env, obs, actions_shape):
        super().init_storage(training_type, num_envs, num_transitions_per_env, obs, actions_shape)
        self.amp_config['rollout_steps'] = num_transitions_per_env

    def _sample_update_inputs(self, size):
        """Same RNG stream as act/sample, smooth noise, expert draw per 256 rows."""
        weights, clips, starts, ratios = [], [], [], []
        mean = torch.zeros(256, self.policy.log_std.numel(), device=self.device)
        std = torch.ones_like(mean)
        for offset in range(0, size, 256):
            n = min(256, size - offset)
            # The old update discarded Normal.sample(); preserve its RNG use.
            torch.normal(mean[:n], std[:n])
            weights.append(2 * torch.rand(n, 1, device=self.device) - 1)
            ids, time, ratio = self.motion_library.sample_window_parameters(n)
            clips.append(ids)
            starts.append(time)
            ratios.append(ratio.expand(n))
        expert = self.motion_library.windows(torch.cat(clips), torch.cat(starts), torch.cat(ratios))
        return torch.cat(weights), expert

    def _paired_training_outputs(self, current, mixed):
        """Encode BOTH images together, never substitute/detach mixed features."""
        latent = self.policy.perception_encoder(torch.cat((current['perception'], mixed['perception'])).float())
        proprio = torch.cat((current['proprio'], mixed['proprio'])).float()
        mean, mixed_mean = self.policy.actor(torch.cat((proprio, latent), -1)).chunk(2)
        value, mixed_value = self.policy.critic(torch.cat((current['critic_state'], mixed['critic_state']))).chunk(2)
        self.policy.distribution = Normal(mean, self.policy.log_std.exp().expand_as(mean))
        return value, mixed_mean, mixed_value

    def update(self):
        self._ensure_motion_library()
        storage = self.storage
        if storage.num_transitions_per_env < 2:
            raise ValueError('Wall10 smoothness needs at least two rollout transitions')
        obs = storage.observations.flatten(0, 1)
        tensors = [x.flatten(0, 1) for x in (storage.actions, storage.values, storage.advantages,
                    storage.returns, storage.actions_log_prob, storage.mu, storage.sigma, storage.dones)]
        motion = self.amp_rollout.flatten(0, 1)
        count = (storage.num_transitions_per_env - 1) * storage.num_envs
        batch_size = count // self.num_mini_batches
        if not batch_size:
            raise ValueError('Wall10 rollout is smaller than its PPO minibatch count')
        permutation = torch.randperm(batch_size * self.num_mini_batches, device=self.device)
        names = ('value_function', 'surrogate', 'entropy', 'amp_loss',
                 'amp_expert_loss', 'amp_policy_loss', 'policy_smooth', 'value_smooth')
        totals = torch.zeros(len(names), device=self.device, dtype=torch.float64)
        execution_size = self.cnn_execution_batch_size
        if execution_size < 256 or execution_size % 256:
            raise ValueError('Wall10 execution batch must be a positive multiple of logical 256')
        updates = 0
        for _ in range(self.num_learning_epochs):
            for indices in permutation.split(batch_size):
                self.optimizer.zero_grad(set_to_none=True)
                kl_total = torch.zeros((), device=self.device, dtype=torch.float64)
                finite_loss = torch.ones((), device=self.device, dtype=torch.bool)
                for ids in indices.split(execution_size):
                    current = {key: obs[key][ids] for key in ('proprio', 'perception', 'critic_state')}
                    actions, old_values, advantages, returns, old_logp, old_mu, old_sigma, done = [x[ids] for x in tensors]
                    weight, expert = self._sample_update_inputs(len(ids))
                    weight *= ~done.bool()
                    following = {key: obs[key][ids + storage.num_envs] for key in current}
                    mixed = {}
                    for key in current:
                        w = weight.reshape(len(ids), *([1] * (current[key].ndim - 1)))
                        mixed[key] = current[key] + w * (following[key] - current[key])
                    value, mixed_mean, mixed_value = self._paired_training_outputs(current, mixed)
                    mean, std = self.policy.action_mean, self.policy.action_std
                    logp = self.policy.get_actions_log_prob(actions)
                    ratio = (logp - old_logp.squeeze(-1)).exp()
                    adv = advantages.squeeze(-1)
                    surrogate = torch.maximum(-adv * ratio, -adv * ratio.clamp(1-self.clip_param, 1+self.clip_param)).mean()
                    value_loss = (value - returns).square()
                    if self.use_clipped_value_loss:
                        clipped = old_values + (value - old_values).clamp(-self.clip_param, self.clip_param)
                        value_loss = torch.maximum(value_loss, (clipped - returns).square())
                    value_loss = value_loss.mean()
                    entropy = self.policy.entropy.mean()
                    policy_smooth = (mean - mixed_mean).square().sum(-1).mean()
                    value_smooth = (value - mixed_value).square().sum(-1).mean()
                    amp_loss, expert_loss, policy_loss = self.amp.compute_loss(motion[ids], expert)
                    loss = (surrogate + self.value_loss_coef * value_loss - self.entropy_coef * entropy
                            + policy_smooth / 9 + value_smooth / 90 + amp_loss)
                    finite_loss &= torch.isfinite(loss.detach())
                    fraction = len(ids) / len(indices)
                    (fraction * loss).backward()
                    with torch.no_grad():
                        kl = (torch.log(std / old_sigma + 1.e-5)
                              + (old_sigma.square() + (old_mu - mean).square()) / (2 * std.square()) - .5).sum(-1).mean()
                        kl_total += fraction * kl.double()
                        totals += fraction * torch.stack((value_loss, surrogate, entropy, amp_loss,
                            expert_loss, policy_loss, policy_smooth, value_smooth)).detach().double()
                # Same full-minibatch KL and single optimizer step; microbatches
                # only bound CNN activation memory and accumulate the gradients.
                if not finite_loss:
                    raise FloatingPointError('Nonfinite wall10 joint PPO/AMP loss')
                kl_total = float(kl_total)
                if self.schedule == 'adaptive':
                    if kl_total > 2 * self.desired_kl:
                        self.learning_rate = max(1.e-5, self.learning_rate / 1.5)
                    elif 0 < kl_total < self.desired_kl / 2:
                        self.learning_rate = min(1.e-2, self.learning_rate * 1.5)
                    for group in self.optimizer.param_groups:
                        group['lr'] = self.learning_rate
                nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm, error_if_nonfinite=True)
                if not torch.stack([torch.isfinite(p.grad).all() for p in self.amp.parameters() if p.grad is not None]).all():
                    raise FloatingPointError('Nonfinite wall10 discriminator gradient')
                self.optimizer.step()
                updates += 1
        storage.clear()
        return dict(zip(names, (totals / updates).tolist()),
                    ppo_learning_rate=self.learning_rate, amp_valid_samples=float(count))


class CarryBoxWall10OnPolicyRunner(CarryBoxOnPolicyRunner):
    def _construct_algorithm(self, obs):
        if (self.policy_cfg.pop('class_name') != 'CarryBoxWall10ActorCritic'
                or self.alg_cfg.pop('class_name') != 'CarryBoxWall10PPO'):
            raise ValueError('Invalid wall10 learning classes')
        policy = CarryBoxWall10ActorCritic(obs, self.cfg['obs_groups'], self.env.num_actions,
                                          **self.policy_cfg).to(self.device)
        algorithm = CarryBoxWall10PPO(policy, device=self.device, multi_gpu_cfg=self.multi_gpu_cfg,
                                      control_dt=self.env.unwrapped.step_dt, **self.alg_cfg)
        algorithm.init_storage('rl', self.env.num_envs, self.num_steps_per_env, obs, [self.env.num_actions])
        return algorithm

    def load(self, path, load_optimizer=True, map_location=None):
        result = super().load(path, load_optimizer, map_location)
        if load_optimizer:
            self.alg.learning_rate = self.alg.optimizer.param_groups[0]['lr']
        return result
