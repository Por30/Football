"""Current-ball uncertainty estimation used by a bounded PPO action branch.

No future-outcome labels and no privileged policy inputs. Confidence is a learned
diagnostic, not a calibrated guarantee. The base depth actor remains active.
"""
from __future__ import annotations

import copy
import math

import torch
from torch import nn

from .algorithm import BallRegressionPPO
from .ball_metrics import ball_prediction_metrics
from .modules import PerceptionActorCritic


def append_ball_feedback(features: torch.Tensor, depth: torch.Tensor,
                         distribution: torch.Tensor) -> torch.Tensor:
    """Shared by live policy and export. Distribution is in normalized units."""
    mean = distribution[:, :6].detach().clamp(-3., 3.)
    logstd = distribution[:, 6:].detach().clamp(-4., 1.)
    visible = ((depth > .1) & (depth < 3. - 1.e-5)).flatten(2).any(-1).to(depth.dtype)
    age = torch.arange(depth.shape[1] - 1, -1, -1, device=depth.device, dtype=depth.dtype)
    recency = (visible * torch.pow(.8, age)).amax(-1, keepdim=True)
    gate = (recency / (1. + logstd.exp().mean(-1, keepdim=True))).clamp(0., 1.)
    return torch.cat((features, mean, logstd, gate), -1)


class BallFeedbackActor(nn.Module):
    def __init__(self, base, feature_dim, proprio_dim, num_actions):
        super().__init__()
        self.base = base
        self.feature_dim = feature_dim
        self.proprio_dim = proprio_dim
        self.residual = nn.Sequential(nn.Linear(proprio_dim + 12, 128), nn.ELU(),
                                      nn.Linear(128, 64), nn.ELU(), nn.Linear(64, num_actions))
        nn.init.zeros_(self.residual[-1].weight)
        nn.init.zeros_(self.residual[-1].bias)

    def forward(self, features):
        raw = features[:, :self.feature_dim]
        estimate = features[:, self.feature_dim:self.feature_dim + 12]
        gate = features[:, -1:]
        correction = .25 * torch.tanh(self.residual(torch.cat((raw[:, :self.proprio_dim], estimate), -1)))
        return self.base(raw) + gate * correction


class StateFeedbackActorCritic(PerceptionActorCritic):
    uses_ball_feedback = True

    def __init__(self, obs, obs_groups, num_actions, **kwargs):
        if obs_groups['policy'] != ['proprio_hist', 'perception']:
            raise ValueError('State feedback requires the v2 proprio/depth policy routing')
        super().__init__(obs, obs_groups, num_actions, **kwargs)
        dim = obs['proprio_hist'].shape[-1] + self.perception_encoder.output_dim
        self.ball_head = nn.Sequential(nn.Linear(dim, 128), nn.ELU(), nn.Linear(128, 12))
        self.actor = BallFeedbackActor(self.actor, dim, obs['proprio_hist'].shape[-1], num_actions)
        self.register_buffer('ball_state_scale', torch.tensor([3., 3., 3., 6., 6., 6.]))

    def _actor_features(self, obs):
        raw = super()._actor_features(obs)
        return append_ball_feedback(raw, obs[self.perception_group], self.ball_head(raw))

    def ball_distribution(self, obs):
        raw = super()._actor_features(obs)
        distribution = self.ball_head(raw)
        return distribution[:, :6], distribution[:, 6:].clamp(-4., 1.)

    def predict_ball_state(self, obs):
        mean, _ = self.ball_distribution(obs)
        return mean * self.ball_state_scale

    def ball_nll(self, obs):
        mean, logstd = self.ball_distribution(obs)
        target = obs[self.privileged_group] / self.ball_state_scale
        return (.5 * ((target - mean) * (-logstd).exp()).square() + logstd).mean()


class StateFeedbackPPO(BallRegressionPPO):
    """One current-state NLL auxiliary stage, with complete-policy KL protection."""

    def __init__(self, policy, *args, **kwargs):
        super().__init__(policy, *args, **kwargs)
        if self.is_multi_gpu or policy.is_recurrent or self.ball_aux_optimizer is None:
            raise ValueError('State feedback requires single-device feedforward PPO and ball auxiliary')
        self.state_feedback_config = dict(schema=1, position_scale_m=3., velocity_scale_m_s=6.,
            logstd_min=-4., logstd_max=1., residual_limit_raw=.25, visibility_near_m=.1,
            visibility_far_m=3., history_decay=.8, aux_coef=self.ball_aux_coef,
            aux_lr=self.ball_aux_optimizer.param_groups[0]['lr'], max_kl=self.ball_aux_max_kl,
            aux_epochs=self.ball_aux_epochs or self.num_learning_epochs, retries=7)
        self.state_feedback_updates = 0

    def _update_ball_head(self):
        flat = self.storage.observations.flatten(0, 1)
        metrics = ball_prediction_metrics(self.policy, flat)
        self.aux_metrics = {'ball/' + key: value for key, value in metrics.items()}
        params = list(self.policy.perception_encoder.parameters()) + list(self.policy.ball_head.parameters())
        optimizer = self.ball_aux_optimizer
        monitor = flat[::max(1, len(flat) // 512)][:512]
        with torch.no_grad():
            stage_mu = self.policy.act_inference(monitor).clone()
            std = (self.policy.std if self.policy.noise_std_type == 'scalar'
                   else self.policy.log_std.exp()).detach().clamp(min=1.e-6)
            _, predicted_logstd = self.policy.ball_distribution(monitor)
            gate = self.policy._actor_features(monitor)[:, -1]
            self.aux_metrics.update({'state_feedback/gate_mean': gate.mean().item(),
                'state_feedback/gate_zero_fraction': (gate == 0).float().mean().item(),
                'state_feedback/position_std_m': (predicted_logstd[:, :3].exp() * 3.).mean().item(),
                'state_feedback/velocity_std_m_s': (predicted_logstd[:, 3:].exp() * 6.).mean().item()})
        accepted = rejected = skipped = attempted = 0
        nll_sum = 0.
        max_trial_kl = 0.
        self.aux_kl = 0.
        base_lr = optimizer.param_groups[0]['lr']
        for batch, *_ in self.storage.mini_batch_generator(
                self.num_mini_batches, self.state_feedback_config['aux_epochs']):
            attempted += 1
            with torch.no_grad():
                old_mu = self.policy.act_inference(batch).clone()
                initial_loss = self.policy.ball_nll(batch)
                if not torch.isfinite(initial_loss):
                    raise FloatingPointError('Non-finite ball-state NLL; auxiliary update aborted')
                nll_sum += initial_loss.item()
            saved_params = [p.detach().clone() for p in params]
            saved_optimizer = copy.deepcopy(optimizer.state_dict())

            def restore():
                with torch.no_grad():
                    for p, saved in zip(params, saved_params):
                        p.copy_(saved)
                optimizer.load_state_dict(copy.deepcopy(saved_optimizer))

            succeeded = False
            for trial in range(7):
                if trial:
                    restore()
                for group in optimizer.param_groups:
                    group['lr'] = base_lr * (.25 ** trial)
                optimizer.zero_grad(set_to_none=True)
                loss = self.policy.ball_nll(batch)
                if not torch.isfinite(loss):
                    restore()
                    raise FloatingPointError('Non-finite ball-state NLL trial')
                (self.ball_aux_coef * loss).backward()
                torch.nn.utils.clip_grad_norm_(params, self.max_grad_norm, error_if_nonfinite=True)
                optimizer.step()
                with torch.no_grad():
                    kl = (.5 * ((self.policy.act_inference(batch) - old_mu) / std).square().sum(-1)).mean().item()
                    stage_kl = (.5 * ((self.policy.act_inference(monitor) - stage_mu) / std).square().sum(-1)).mean().item()
                max_trial_kl = max(max_trial_kl, kl)
                if (math.isfinite(kl) and math.isfinite(stage_kl)
                        and max(kl, stage_kl) <= self.ball_aux_max_kl):
                    accepted += 1
                    self.state_feedback_updates += 1
                    self.aux_kl = max(self.aux_kl, kl)
                    succeeded = True
                    break
                rejected += 1
            if not succeeded:
                # Even head-only training changes actions now. Restore and skip entirely.
                restore()
                optimizer.zero_grad(set_to_none=True)
                skipped += 1
            for group in optimizer.param_groups:
                group['lr'] = base_lr
        with torch.no_grad():
            stage_kl = (.5 * ((self.policy.act_inference(monitor) - stage_mu) / std).square().sum(-1)).mean().item()
            f = self.policy._actor_features(monitor)
            delta = self.policy.actor(f) - self.policy.actor.base(f[:, :self.policy.actor.feature_dim])
        self.aux_metrics.update({'state_feedback/nll': nll_sum / max(attempted, 1),
            'state_feedback/residual_abs_mean_raw': delta.abs().mean().item(),
            'state_feedback/residual_abs_max_raw': delta.abs().max().item(),
            'state_feedback/total_aux_updates': self.state_feedback_updates,
            'aux/attempted_batches': attempted, 'aux/encoder_updates': accepted,
            'aux/rejected_trials': rejected, 'aux/skipped_batches': skipped,
            'aux/head_only_batches': 0, 'aux/trial_max_kl': max_trial_kl,
            'aux/stage_monitor_kl': stage_kl, 'aux/monitor_count': len(monitor), 'aux/base_lr': base_lr})
        return metrics['mse']
