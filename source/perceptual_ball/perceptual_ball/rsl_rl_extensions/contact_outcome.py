"""V3-only, training-time short-horizon outcome learning; no reference tracking.

Targets follow the sampled rollout policy after its first (conditioned) action.
They are not counterfactual contact outcomes or calibrated recovery probabilities.
"""
from __future__ import annotations

import copy
import math

import torch
from torch import nn
from torch.nn import functional as F

from .algorithm import BallRegressionPPO
from .modules import PerceptionActorCritic


def build_outcome_targets(states, dones, horizon):
    """Return [T-H,N,6] targets and a valid mask BEFORE flattening/shuffling.

    State columns: cumulative serves, cumulative kick proxies, world ball vx/vy,
    yaw cos/sin, body gravity x/y, root height above ground, ball active.
    obs[t] precedes action[t]; dones[t] belongs to that action's transition.
    No terminal snapshots are needed: every window containing a done is excluded.
    """
    if states.ndim != 3 or states.shape[-1] != 10 or horizon < 1:
        raise ValueError("Expected [time, env, 10] outcome state and positive horizon")
    if dones.shape not in (states.shape[:2], (*states.shape[:2], 1)):
        raise ValueError("Outcome dones must match rollout time/environment dimensions")
    count = max(0, states.shape[0] - horizon)
    source, future = states[:count], states[horizon:horizon + count]
    targets = states.new_zeros((count, states.shape[1], 6), dtype=torch.float32)
    c, s = source[..., 4], source[..., 5]
    targets[..., 0] = c * future[..., 2] + s * future[..., 3]
    targets[..., 1] = -s * future[..., 2] + c * future[..., 3]
    targets[..., 2:5] = future[..., 6:9]
    targets[..., 5] = (future[..., 1] > source[..., 1]).float()
    valid = source[..., 9] > .5
    done = dones.reshape(states.shape[:2]).bool()
    for offset in range(horizon + 1):
        row = states[offset:offset + count]
        valid &= torch.isfinite(row).all(-1) & (row[..., 0] == source[..., 0])
        if offset < horizon:
            valid &= ~done[offset:offset + count]
    valid &= torch.isfinite(targets).all(-1)
    return targets, valid


class OutcomeActorCritic(PerceptionActorCritic):
    """Same inference actor as v2, plus a head used only during training."""

    def __init__(self, obs, obs_groups, num_actions, **kwargs):
        if any("outcome_state" in groups for groups in obs_groups.values()):
            raise ValueError("outcome_state is supervision only, never an actor/critic input")
        super().__init__(obs, obs_groups, num_actions, **kwargs)
        features = self.perception_encoder.output_dim + sum(
            obs[g].shape[-1] for g in obs_groups["policy"] if g != self.perception_group)
        self.outcome_head = nn.Sequential(
            nn.Linear(features + num_actions, 128), nn.ELU(),
            nn.Linear(128, 64), nn.ELU(), nn.Linear(64, 6))

    def predict_outcome(self, obs, actions):
        # No true ball state, future actions, serve ID or target is read here.
        return self.outcome_head(torch.cat((self._actor_features(obs), actions.detach()), -1))


class ContactOutcomePPO(BallRegressionPPO):
    """An optional auxiliary stage after unchanged v2 PPO/ball/AMP updates."""

    def __init__(self, policy, *args, outcome_aux_coef=.1, outcome_aux_lr=1.e-4,
                 outcome_horizon=8, outcome_max_samples=8192, outcome_batch_size=2048,
                 outcome_max_kl=.005, **kwargs):
        for name, value in (("horizon", outcome_horizon), ("max_samples", outcome_max_samples),
                            ("batch_size", outcome_batch_size)):
            if type(value) is not int or value <= 0:
                raise ValueError("outcome " + name + " must be a positive integer")
        if (not all(math.isfinite(x) for x in (outcome_aux_coef, outcome_aux_lr, outcome_max_kl))
                or outcome_aux_coef < 0 or outcome_aux_lr <= 0 or outcome_max_kl < 0):
            raise ValueError("Invalid outcome coefficient, learning rate or KL bound")
        super().__init__(policy, *args, **kwargs)
        if self.is_multi_gpu or policy.is_recurrent:
            raise ValueError("ContactOutcomePPO currently supports a single GPU, feedforward policy")
        self.outcome_config = dict(schema=1, horizon=outcome_horizon, coef=outcome_aux_coef,
                                  lr=outcome_aux_lr, max_samples=outcome_max_samples,
                                  batch_size=outcome_batch_size, max_kl=outcome_max_kl)
        self.outcome_optimizer = (torch.optim.Adam(
            list(policy.perception_encoder.parameters()) + list(policy.outcome_head.parameters()),
            lr=outcome_aux_lr) if outcome_aux_coef > 0 else None)

    def init_storage(self, training_type, num_envs, num_transitions_per_env, obs, actions_shape):
        if "outcome_state" not in obs or obs["outcome_state"].shape[-1] != 10:
            raise ValueError("V3 requires its training-only 10-column outcome_state")
        if self.outcome_optimizer is not None and num_transitions_per_env <= self.outcome_config["horizon"]:
            raise ValueError("Outcome rollout must be longer than its prediction horizon")
        super().init_storage(training_type, num_envs, num_transitions_per_env, obs, actions_shape)

    def update(self):
        losses = super().update()
        if self.outcome_optimizer is not None:
            losses.update(self._update_outcome())
        return losses

    @staticmethod
    def _loss(pred, target, positive_weight):
        # Output units: ball vx/vy divided by 6 m/s, gravity x/y, (height-.8)/.2 m,
        # and a kick-proxy logit. Balance the two physical result groups explicitly.
        ball = F.smooth_l1_loss(pred[:, :2], target[:, :2] / 6.)
        body_target = torch.cat((target[:, 2:4], (target[:, 4:5] - .8) / .2), -1)
        body = F.smooth_l1_loss(pred[:, 2:5], body_target)
        event = F.binary_cross_entropy_with_logits(pred[:, 5], target[:, 5], pos_weight=positive_weight)
        return .5 * ball + .5 * body + .2 * event

    def _update_outcome(self):
        cfg = self.outcome_config
        targets, valid = build_outcome_targets(
            self.storage.observations["outcome_state"], self.storage.dones, cfg["horizon"])
        flat = self.storage.observations[:valid.shape[0]].flatten(0, 1)
        actions = self.storage.actions[:valid.shape[0]].flatten(0, 1)
        targets = targets.flatten(0, 1)
        valid = valid.flatten()
        # Corrupt source inputs must not contaminate either auxiliary gradients or KL monitors.
        finite = torch.isfinite(actions).all(-1)
        for group in self.policy.obs_groups["policy"]:
            finite &= torch.isfinite(flat[group]).flatten(1).all(-1)
        metrics = {"outcome/eligible_count": valid.sum().item(),
                   "outcome/nonfinite_source_count": (~finite).sum().item(),
                   "outcome/nonfinite_state_count": (~torch.isfinite(
                       self.storage.observations["outcome_state"]).all(-1)).sum().item(),
                   "outcome/horizon_steps": cfg["horizon"]}
        valid &= finite
        ids = valid.nonzero(as_tuple=False).flatten()
        metrics["outcome/valid_count"] = len(ids)
        metrics["outcome/skipped"] = float(len(ids) == 0)
        if len(ids) == 0:
            return metrics
        ids = ids[torch.randperm(len(ids), device=ids.device)[:cfg["max_samples"]]]
        # Include finite inactive states as well: an auxiliary update must also preserve standing.
        monitor_ids = finite.nonzero(as_tuple=False).flatten()
        monitor_ids = monitor_ids[::max(1, len(monitor_ids) // 256)][:256]
        monitor = flat[monitor_ids]
        with torch.no_grad():
            stage_mu = self.policy.act_inference(monitor).clone()
            std = (self.policy.std if self.policy.noise_std_type == "scalar"
                   else self.policy.log_std.exp()).detach().clamp(min=1.e-6)
        encoder = list(self.policy.perception_encoder.parameters())
        head = list(self.policy.outcome_head.parameters())
        params = encoder + head
        optimizer = self.outcome_optimizer
        base_lr = optimizer.param_groups[0]["lr"]
        positive = targets[ids, 5].sum()
        positive_weight = ((len(ids) - positive) / positive.clamp(min=1)).clamp(1., 20.)
        sums = dict(loss=0., ball_sq=0., gravity_sq=0., height_sq=0., brier=0.)
        accepted = rejected = fallback = 0
        max_batch_kl = 0.
        for batch_ids in ids.split(cfg["batch_size"]):
            batch, action, target = flat[batch_ids], actions[batch_ids], targets[batch_ids]
            with torch.no_grad():
                old_mu = self.policy.act_inference(batch).clone()
                pred = self.policy.predict_outcome(batch, action)
                n = len(batch_ids)
                sums["loss"] += self._loss(pred, target, positive_weight).item() * n
                sums["ball_sq"] += (pred[:, :2] * 6. - target[:, :2]).square().sum().item()
                sums["gravity_sq"] += (pred[:, 2:4] - target[:, 2:4]).square().sum().item()
                sums["height_sq"] += (pred[:, 4] * .2 + .8 - target[:, 4]).square().sum().item()
                sums["brier"] += (pred[:, 5].sigmoid() - target[:, 5]).square().sum().item()
            saved_params = [p.detach().clone() for p in params]
            saved_optimizer = copy.deepcopy(optimizer.state_dict())

            def restore():
                with torch.no_grad():
                    for p, saved in zip(params, saved_params):
                        p.copy_(saved)
                # Adam may reuse tensors from load_state_dict; trials must not mutate
                # the snapshot that subsequent retries/head-only fallback restore.
                optimizer.load_state_dict(copy.deepcopy(saved_optimizer))

            succeeded = False
            for trial in range(4):
                if trial:
                    restore()
                for group in optimizer.param_groups:
                    group["lr"] = base_lr * (.25 ** trial)
                optimizer.zero_grad(set_to_none=True)
                loss = self._loss(self.policy.predict_outcome(batch, action), target, positive_weight)
                (cfg["coef"] * loss).backward()
                torch.nn.utils.clip_grad_norm_(params, self.max_grad_norm, error_if_nonfinite=True)
                optimizer.step()
                with torch.no_grad():
                    batch_kl = (.5 * ((self.policy.act_inference(batch) - old_mu) / std).square().sum(-1)).mean().item()
                    stage_kl = (.5 * ((self.policy.act_inference(monitor) - stage_mu) / std).square().sum(-1)).mean().item()
                if (math.isfinite(batch_kl) and math.isfinite(stage_kl)
                        and max(batch_kl, stage_kl) <= cfg["max_kl"]):
                    accepted += 1
                    max_batch_kl = max(max_batch_kl, batch_kl)
                    succeeded = True
                    break
                rejected += 1
            if not succeeded:
                restore()
                optimizer.zero_grad(set_to_none=True)
                loss = self._loss(self.policy.predict_outcome(batch, action), target, positive_weight)
                (cfg["coef"] * loss).backward()
                # grad=None also prevents stale Adam momentum moving the encoder.
                for p in encoder:
                    p.grad = None
                torch.nn.utils.clip_grad_norm_(head, self.max_grad_norm, error_if_nonfinite=True)
                optimizer.step()
                fallback += 1
            for group in optimizer.param_groups:
                group["lr"] = base_lr
        with torch.no_grad():
            stage_kl = (.5 * ((self.policy.act_inference(monitor) - stage_mu) / std).square().sum(-1)).mean().item()
        count = len(ids)
        metrics.update({"outcome/loss": sums["loss"] / count,
                        "outcome/ball_velocity_vector_rmse_m_s": math.sqrt(sums["ball_sq"] / count),
                        "outcome/gravity_xy_vector_rmse": math.sqrt(sums["gravity_sq"] / count),
                        "outcome/height_rmse_m": math.sqrt(sums["height_sq"] / count),
                        "outcome/kick_proxy_brier": sums["brier"] / count,
                        "outcome/kick_proxy_positive_fraction": positive.item() / count,
                        "outcome/sample_count": count, "outcome/encoder_updates": accepted,
                        "outcome/rejected_trials": rejected, "outcome/head_only_batches": fallback,
                        "outcome/max_accepted_batch_kl": max_batch_kl,
                        "outcome/stage_monitor_kl": stage_kl})
        return metrics
