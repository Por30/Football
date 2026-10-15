"""Depth-only exteroception, symmetric critic, and joint PPO/box-pose supervision."""
from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Normal
from rsl_rl.modules import ActorCritic
from rsl_rl.networks import MLP
from rsl_rl.algorithms import PPO
from rsl_rl.runners import OnPolicyRunner
from .modules import DepthCNNEncoder
from .amp import AMP
from perceptual_ball.carrybox_amp import AMP_WINDOW, AMP_FRAME_DIM, DEFAULT_DATASET_PATH, FindBoxMotionLibrary


def square_box_symmetries(device, dtype):
    """Eight proper rotations preserving a .30 x .30 x .25 box (D4)."""
    rotations = []
    for c, s in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        rz = torch.tensor([[c, -s, 0], [s, c, 0], [0, 0, 1]], device=device, dtype=dtype)
        rotations.extend((rz, rz @ torch.diag(torch.tensor([1, -1, -1], device=device, dtype=dtype))))
    return torch.stack(rotations)


def box_pose_loss(prediction, target):
    """xyz in camera optical frame (m), then first two rotation columns (6D).

    The rotation is identifiable only modulo the untextured square box's D4 symmetry.
    Regression uses equivalent 6D targets, avoiding quaternion sign discontinuities.
    """
    target = target.detach()
    x, y = target[:, 3:6], target[:, 6:9]
    rotation = torch.stack((x, y, torch.linalg.cross(x, y)), dim=-1)
    candidates = rotation[:, None] @ square_box_symmetries(target.device, target.dtype)[None]
    candidates = candidates[..., :2].transpose(-1, -2).flatten(-2)
    position = (prediction[:, :3] - target[:, :3]).square().mean()
    orientation = (prediction[:, None, 3:] - candidates).square().mean(-1).min(-1).values.mean()
    return position, orientation


class CarryBoxActorCritic(ActorCritic):
    def __init__(self, obs, obs_groups, num_actions, actor_hidden_dims=(256, 128),
                 critic_hidden_dims=(256, 128), activation='elu', init_noise_std=.5,
                 actor_obs_normalization=False, critic_obs_normalization=False,
                 noise_std_type='log', **kwargs):
        nn.Module.__init__(self)
        expected = ['proprio', 'perception']
        if obs_groups.get('policy') != expected or obs_groups.get('critic') != expected:
            raise ValueError('CarryBox actor and critic require exactly proprio + perception; no privileged inputs')
        if actor_obs_normalization or critic_obs_normalization or noise_std_type != 'log' or kwargs:
            raise ValueError('CarryBox requires unnormalized inputs, log std, and its explicit policy schema')
        self.obs_groups = obs_groups
        self.perception_group = 'perception'
        self.actor_obs_normalization = self.critic_obs_normalization = False
        self.actor_obs_normalizer = self.critic_obs_normalizer = nn.Identity()
        self.perception_encoder = DepthCNNEncoder(*obs['perception'].shape[1:])
        dim = obs['proprio'].shape[-1] + self.perception_encoder.output_dim
        self.actor = MLP(dim, num_actions, list(actor_hidden_dims), activation)
        self.critic = MLP(dim, 1, list(critic_hidden_dims), activation)
        self.pose_head = nn.Sequential(nn.Linear(self.perception_encoder.output_dim, 128), nn.ELU(), nn.Linear(128, 9))
        self.log_std = nn.Parameter(torch.full((num_actions,), float(torch.log(torch.tensor(init_noise_std)))))
        self.noise_std_type = 'log'
        self.distribution = None

    def _features(self, obs):
        return torch.cat((obs['proprio'], self.perception_encoder(obs['perception'])), -1)

    def update_distribution(self, obs):
        mean = self.actor(self._features(obs))
        self.distribution = Normal(mean, self.log_std.exp().expand_as(mean))

    def act(self, obs, **kwargs):
        self.update_distribution(obs)
        return self.distribution.sample()

    def act_inference(self, obs):
        return self.actor(self._features(obs))

    def evaluate(self, obs, **kwargs):
        return self.critic(self._features(obs))

    def predict_box_pose(self, obs):
        return self.pose_head(self.perception_encoder(obs['perception']))


class CarryBoxPPO(PPO):
    """RSL-RL PPO update with pose loss in the SAME minibatch/optimizer step.

    Kept explicit because installed RSL-RL 3.0.1 has no auxiliary-loss hook. Unsupported
    augmentation/distributed options fail loudly rather than silently misaligning labels.
    """
    def __init__(self, policy, *args, pose_aux_coef=.5, amp_coef=0., amp_reward_scale=2.,
                 amp_lr=1.e-4, amp_data_dir=DEFAULT_DATASET_PATH, control_dt=.02, **kwargs):
        super().__init__(policy, *args, **kwargs)
        if self.rnd or self.symmetry or self.is_multi_gpu or self.schedule != 'fixed':
            raise ValueError('CarryBox supports single-device fixed-schedule PPO without RND/symmetry augmentation')
        self.pose_aux_coef = pose_aux_coef
        if not 0. <= amp_coef <= 1. or amp_reward_scale <= 0. or control_dt <= 0.:
            raise ValueError('Invalid AMP reward coefficient or control timestep')
        self.amp_data_dir = amp_data_dir
        self.control_dt = control_dt
        self.amp_config = dict(schema=1, coef=amp_coef, reward_scale=amp_reward_scale,
                               control_dt=control_dt, window_length=AMP_WINDOW, frame_dim=AMP_FRAME_DIM)
        self.motion_library = None  # loaded only when collecting training transitions
        self.motion_metadata = None
        self.amp_statistics_initialized = False
        self.amp = AMP(AMP_WINDOW * AMP_FRAME_DIM).to(self.device) if amp_coef else None
        self.amp_optimizer = torch.optim.Adam(self.amp.parameters(), lr=amp_lr) if self.amp is not None else None

    def init_storage(self, training_type, num_envs, num_transitions_per_env, obs, actions_shape):
        super().init_storage(training_type, num_envs, num_transitions_per_env, obs, actions_shape)
        if self.amp is not None:
            if obs['amp'].shape != (num_envs, AMP_WINDOW * AMP_FRAME_DIM):
                raise ValueError('CarryBox AMP requires 10 x 64 motion observations')
            self.amp_rollout = torch.zeros(num_transitions_per_env, num_envs, AMP_WINDOW * AMP_FRAME_DIM, device=self.device)
            self.amp_valid = torch.zeros(num_transitions_per_env, num_envs, dtype=torch.bool, device=self.device)
            self.amp_age = torch.zeros(num_envs, dtype=torch.long, device=self.device)

    def _ensure_motion_library(self):
        if self.motion_library is None:
            library = FindBoxMotionLibrary(self.amp_data_dir, device=self.device, env_fps=1. / self.control_dt)
            if self.motion_metadata is not None and self.motion_metadata != library.metadata:
                raise ValueError('AMP resume dataset/schema differs from checkpoint')
            self.motion_library = library
            self.motion_metadata = library.metadata
        if not self.amp_statistics_initialized:
            self.amp.set_statistics(self.motion_library.sample_expert_amp_obs(2048))
            self.amp_statistics_initialized = True

    def _process_amp(self, obs, rewards, dones, extras):
        self._ensure_motion_library()
        motion = obs['amp'].detach().clone()
        if dones.any():
            terminal = extras.get('terminal_observations')
            if terminal is None or 'amp' not in terminal['obs']:
                raise RuntimeError('CarryBox AMP requires pre-reset terminal motion for all done transitions')
            ids = terminal['env_ids'].to(self.device)
            motion[ids] = terminal['obs']['amp'].to(self.device)
        if not torch.isfinite(motion).all():
            raise FloatingPointError('Non-finite live AMP motion')
        self.amp_age += 1
        valid = self.amp_age >= AMP_WINDOW - 1  # reset provides the first real frame
        index = self.storage.step
        self.amp_rollout[index].copy_(motion)
        self.amp_valid[index].copy_(valid)
        self.amp_age[dones.bool().flatten()] = 0
        style = self.amp.predict_reward(motion)
        coef = self.amp_config['coef']
        shaped = ((1. - coef) * rewards
                  + coef * self.control_dt * self.amp_config['reward_scale'] * style)
        rewards = torch.where(valid, shaped, rewards)
        extras.setdefault('log', {}).update({
            'AMP/style_reward': style[valid].mean().item() if valid.any() else 0.,
            'AMP/valid_fraction': valid.float().mean().item(),
        })
        return rewards

    def process_env_step(self, obs, rewards, dones, extras):
        extras = dict(extras)
        if self.amp is not None:
            rewards = self._process_amp(obs, rewards, dones, extras)
        timeouts = extras.pop('time_outs', None)
        if timeouts is not None and timeouts.any():
            terminal = extras.get('terminal_observations')
            if terminal is None:
                raise RuntimeError('CarryBox timeout needs the pre-reset depth/proprio history')
            ids = terminal['env_ids'].to(self.device)
            with torch.no_grad():
                values = self.policy.evaluate({k: v.to(self.device) for k, v in terminal['obs'].items()}).squeeze(-1)
            rewards = rewards.clone()
            rewards[ids] += self.gamma * values * timeouts[ids].to(self.device)
        super().process_env_step(obs, rewards, dones, extras)

    def update(self):
        totals = dict(value_function=0., surrogate=0., entropy=0., box_position=0., box_rotation=0.)
        count = 0
        for batch in self.storage.mini_batch_generator(self.num_mini_batches, self.num_learning_epochs):
            obs, actions, old_values, advantages, returns, old_logp, *_ = batch
            if self.normalize_advantage_per_mini_batch:
                advantages = (advantages - advantages.mean()) / (advantages.std() + 1.e-8)
            self.policy.act(obs)
            logp = self.policy.get_actions_log_prob(actions)
            values = self.policy.evaluate(obs)
            ratio = (logp - old_logp.squeeze(-1)).exp()
            adv = advantages.squeeze(-1)
            surrogate = torch.maximum(-adv * ratio, -adv * ratio.clamp(1-self.clip_param, 1+self.clip_param)).mean()
            value_loss = (values - returns).square()
            if self.use_clipped_value_loss:
                clipped = old_values + (values - old_values).clamp(-self.clip_param, self.clip_param)
                value_loss = torch.maximum(value_loss, (clipped - returns).square())
            value_loss = value_loss.mean()
            entropy = self.policy.entropy.mean()
            position, rotation = box_pose_loss(self.policy.predict_box_pose(obs), obs['box_pose_target'])
            loss = surrogate + self.value_loss_coef * value_loss - self.entropy_coef * entropy
            loss = loss + self.pose_aux_coef * (position + rotation)
            if not torch.isfinite(loss):
                raise FloatingPointError('Non-finite CarryBox training loss')
            self.optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm, error_if_nonfinite=True)
            self.optimizer.step()
            with torch.no_grad():
                self.policy.log_std.clamp_(-5., 1.)
            for key, value in zip(totals, (value_loss, surrogate, entropy, position, rotation)):
                totals[key] += value.item()
            count += 1
        self.storage.clear()
        result = {key: value / count for key, value in totals.items()}
        if self.amp is not None:
            result.update(self._update_amp())
        return result

    def _update_amp(self):
        policy_motion = self.amp_rollout[self.amp_valid].detach()
        if not len(policy_motion):
            return {'amp_loss': 0., 'amp_expert_loss': 0., 'amp_policy_loss': 0., 'amp_valid_samples': 0.}
        totals = torch.zeros(3, device=self.device)
        count = 0
        for _ in range(self.num_learning_epochs):
            permutation = torch.randperm(len(policy_motion), device=self.device)
            for indices in permutation.tensor_split(self.num_mini_batches):
                if not len(indices):
                    continue
                expert = self.motion_library.sample_expert_amp_obs(len(indices))
                loss, expert_loss, policy_loss = self.amp.compute_loss(policy_motion[indices], expert)
                if not torch.isfinite(loss):
                    raise FloatingPointError('Non-finite CarryBox AMP loss')
                self.amp_optimizer.zero_grad(set_to_none=True)
                loss.backward()
                nn.utils.clip_grad_norm_(self.amp.parameters(), 10., error_if_nonfinite=True)
                self.amp_optimizer.step()
                totals += torch.stack((loss, expert_loss, policy_loss)).detach()
                count += 1
        values = (totals / count).tolist()
        return dict(zip(('amp_loss', 'amp_expert_loss', 'amp_policy_loss'), values), amp_valid_samples=float(len(policy_motion)))


class CarryBoxOnPolicyRunner(OnPolicyRunner):
    def _construct_algorithm(self, obs):
        if self.policy_cfg.pop('class_name') != 'CarryBoxActorCritic' or self.alg_cfg.pop('class_name') != 'CarryBoxPPO':
            raise ValueError('Invalid CarryBox learning classes')
        policy = CarryBoxActorCritic(obs, self.cfg['obs_groups'], self.env.num_actions, **self.policy_cfg).to(self.device)
        alg = CarryBoxPPO(policy, device=self.device, multi_gpu_cfg=self.multi_gpu_cfg,
                         control_dt=self.env.unwrapped.step_dt, **self.alg_cfg)
        alg.init_storage('rl', self.env.num_envs, self.num_steps_per_env, obs, [self.env.num_actions])
        return alg

    def environment_contract(self):
        env = getattr(getattr(self, 'env', None), 'unwrapped', None)
        return env.checkpoint_contract() if hasattr(env, 'checkpoint_contract') else None

    def learn(self, num_learning_iterations, init_at_random_ep_len=False):
        env = self.env.unwrapped
        if not hasattr(env, 'set_training_iteration'):
            return super().learn(num_learning_iterations, init_at_random_ep_len)
        iteration = self.current_learning_iteration
        env.set_training_iteration(iteration)
        original_update = self.alg.update
        def update_with_iteration():
            nonlocal iteration
            result = original_update()
            iteration += 1
            env.set_training_iteration(iteration)
            return result
        self.alg.update = update_with_iteration
        try:
            return super().learn(num_learning_iterations, init_at_random_ep_len)
        finally:
            self.alg.update = original_update

    def warm_start(self, path):
        """Explicit weights-only transfer: policy + auxiliary head, fresh PPO/AMP/curriculum."""
        if self.environment_contract() is None:
            raise ValueError('CarryBox warm-start is supported only for wall variants')
        if self.alg.optimizer.state or self.alg.amp_statistics_initialized:
            raise ValueError('CarryBox warm-start requires a fresh runner/optimizers')
        state = torch.load(path, map_location=self.device, weights_only=False)
        if state.get('carrybox_schema') != 2:
            raise ValueError('CarryBox warm-start requires schema=2')
        model = state.get('model_state_dict', {})
        expected = self.alg.policy.state_dict()
        if (model.keys() != expected.keys() or any(model[k].shape != v.shape or
                not torch.isfinite(model[k]).all() for k, v in expected.items())):
            raise ValueError('Incompatible CarryBox warm-start model shapes/values')
        self.alg.policy.load_state_dict(model)
        self.current_learning_iteration = 0
        self.warm_start_info = dict(source=str(path), source_environment=state.get('environment_contract'),
                                    transfer='policy_encoder_actor_critic_pose_head', fresh='PPO_AMP_curriculum')

    def save(self, path, infos=None):
        state = dict(model_state_dict=self.alg.policy.state_dict(), optimizer_state_dict=self.alg.optimizer.state_dict(),
                     iter=self.current_learning_iteration, infos=infos, carrybox_schema=2,
                     pose_aux_coef=self.alg.pose_aux_coef, torch_rng_state=torch.get_rng_state())
        state['environment_contract'] = self.environment_contract()
        state['amp'] = dict(config=self.alg.amp_config, dataset=self.alg.motion_metadata,
                            statistics_initialized=self.alg.amp_statistics_initialized,
                            model=self.alg.amp.state_dict() if self.alg.amp is not None else None,
                            optimizer=self.alg.amp_optimizer.state_dict() if self.alg.amp_optimizer is not None else None)
        if torch.cuda.is_available():
            state['cuda_rng_state'] = torch.cuda.get_rng_state_all()
        torch.save(state, path)
        if getattr(self, 'logger_type', None) in ('neptune', 'wandb') and not self.disable_logs:
            self.writer.save_model(path, self.current_learning_iteration)

    def load(self, path, load_optimizer=True, map_location=None):
        state = torch.load(path, map_location=map_location or self.device, weights_only=False)
        if state.get('environment_contract') != self.environment_contract():
            raise ValueError('Incompatible CarryBox environment variant/contract; use explicit warm-start for transfer')
        if state.get('carrybox_schema') != 2 or state.get('pose_aux_coef') != self.alg.pose_aux_coef:
            raise ValueError('Incompatible CarryBox checkpoint/schema/auxiliary objective')
        amp = state.get('amp', {})
        if amp.get('config') != self.alg.amp_config:
            raise ValueError('Incompatible CarryBox AMP objective')
        if self.alg.amp is not None:
            model = amp.get('model')
            expected = self.alg.amp.state_dict()
            optimizer = amp.get('optimizer')
            if (not isinstance(model, dict) or model.keys() != expected.keys()
                    or any(model[k].shape != v.shape or not torch.isfinite(model[k]).all() for k, v in expected.items())
                    or type(amp.get('statistics_initialized')) is not bool
                    or (amp['statistics_initialized'] and not isinstance(amp.get('dataset'), dict))):
                raise ValueError('Missing or incompatible AMP state/statistics/dataset identity')
            if load_optimizer and (not isinstance(optimizer, dict) or not {'state', 'param_groups'} <= optimizer.keys()):
                raise ValueError('Missing AMP optimizer state')
        if not all(torch.isfinite(value).all() for value in state['model_state_dict'].values()):
            raise ValueError('Non-finite CarryBox checkpoint')
        infos = super().load(path, load_optimizer=load_optimizer, map_location=map_location or self.device)
        if self.alg.amp is not None:
            self.alg.amp.load_state_dict(amp['model'])
            self.alg.amp_statistics_initialized = amp['statistics_initialized']
            self.alg.motion_metadata = amp['dataset']
            self.alg.motion_library = None  # validate dataset lazily if training resumes; play needs no dataset
            self.alg.amp_age.zero_()  # in-flight physics/windows are not part of checkpoint
            if load_optimizer:
                self.alg.amp_optimizer.load_state_dict(amp['optimizer'])
        if load_optimizer:
            torch.set_rng_state(state['torch_rng_state'].cpu())
            if torch.cuda.is_available() and 'cuda_rng_state' in state:
                torch.cuda.set_rng_state_all([s.cpu() for s in state['cuda_rng_state']])
        return infos
