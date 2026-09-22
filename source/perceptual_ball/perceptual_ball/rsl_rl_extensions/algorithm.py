# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from itertools import chain
import copy

import torch
import torch.nn.functional as F
import torch.optim as optim

from rsl_rl.algorithms import PPO

from .amp import AMP, SkillAMP
from .ball_metrics import ball_prediction_metrics


class BallRegressionPPO(PPO):
    """PPO plus two auxiliary pieces, both optional and independently switchable:

    1. A supervised loss that trains `PerceptionActorCritic`'s perception encoder to regress the
       ball's true (privileged) position/velocity (`ball_aux_coef`).
    2. An AMP discriminator (`amp_coef`, `motion_library`) that scores whether a window of the
       robot's own recent motion (the env's "amp" obs group) looks like the reference kick
       clips, mixing that score into the task reward -- ported from PhysHSI's `HIMPPO`
       (/home/cao/PhysHSI/rsl_rl/rsl_rl/algorithms/him_ppo.py): `reward = amp_coef * (amp_reward
       * amp_reward_scale) + (1 - amp_coef) * task_reward`.

    Both pieces get their own optimizer and their own pass over the just-collected rollout, run
    right after the standard PPO update -- the same "side loss with its own optimizer" shape
    rsl_rl already uses for RND, just with different targets. `rsl_rl.storage.RolloutStorage.clear()`
    only resets an internal step counter, so the rollout tensors `super().update()` already
    consumed are still valid to read again here.
    """

    def __init__(
        self,
        policy,
        *args,
        ball_aux_coef: float = 0.5,
        ball_aux_lr: float = 1.0e-3,
        ball_aux_max_kl: float = 0.01,
        ball_aux_backtracking: bool = False,
        ball_aux_epochs: int | None = None,
        motion_library=None,
        amp_obs_group: str = "amp",
        amp_coef: float = 0.25,
        amp_reward_scale: float = 0.5,
        amp_lr: float = 1.0e-3,
        **kwargs,
    ):
        super().__init__(policy, *args, **kwargs)
        self.ball_aux_coef = ball_aux_coef
        self.ball_aux_max_kl = ball_aux_max_kl
        self.ball_aux_backtracking = ball_aux_backtracking
        self.ball_aux_epochs = ball_aux_epochs
        self.aux_metrics = {}
        self.aux_kl = 0.0
        if ball_aux_coef > 0.0:
            self.ball_aux_optimizer = optim.Adam(
                chain(self.policy.perception_encoder.parameters(), self.policy.ball_head.parameters()),
                lr=ball_aux_lr,
            )
        else:
            self.ball_aux_optimizer = None

        self.motion_library = motion_library
        self.amp_obs_group = amp_obs_group
        self.amp_coef = amp_coef
        self.amp_reward_scale = amp_reward_scale
        self.amp_lr = amp_lr
        self.amp: AMP | None = None  # constructed lazily in init_storage, once obs dims are known

    def init_storage(self, training_type, num_envs, num_transitions_per_env, obs, actions_shape):
        super().init_storage(training_type, num_envs, num_transitions_per_env, obs, actions_shape)
        if self.motion_library is not None and self.amp is None:
            self.amp = AMP(num_obs=obs[self.amp_obs_group].shape[-1]).to(self.device)
            self.amp.set_statistics(self.motion_library.sample_expert_amp_obs(2048))
            self.amp_optimizer = optim.Adam(self.amp.parameters(), lr=self.amp_lr)

    def _score_amp(self, amp_obs, obs):
        return self.amp.predict_reward(amp_obs)

    def process_env_step(self, obs, rewards, dones, extras):
        terminal = extras.get("terminal_observations")
        if dones.any() and terminal is None:
            raise RuntimeError("SoccerEnv terminal_observations required for done transitions")
        amp_obs = obs[self.amp_obs_group].clone()
        if terminal is not None:
            ids = terminal["env_ids"].to(amp_obs.device)
            amp_obs[ids] = terminal["obs"][self.amp_obs_group].to(amp_obs.device)
        if self.amp is not None:
            amp_reward = self._score_amp(amp_obs, self.transition.observations)
            rewards = (1.0 - self.amp_coef) * rewards + self.amp_coef * self.amp_reward_scale * amp_reward.view_as(rewards)
            extras.setdefault("log", {}).update({
                "AMP/reward_mean": amp_reward.mean().item(),
                "AMP/reward_zero_fraction": (amp_reward == 0).float().mean().item(),
            })
        # Replace RSL-RL's pre-action-value timeout bootstrap with terminal V, once.
        extras = dict(extras)
        timeouts = extras.pop("time_outs", None)
        if timeouts is not None and timeouts.any():
            if terminal is None:
                raise RuntimeError("Timeout requires a pre-reset critic observation")
            terminal_obs = {k: v.to(self.device) for k, v in terminal["obs"].items()}
            ids = terminal["env_ids"].to(self.device)
            # Critic routing uses the same action-time skill as this transition's AMP.
            if "skill" in self.transition.observations:
                terminal_obs["skill"] = self.transition.observations["skill"][ids]
            with torch.no_grad():
                values = self.policy.evaluate(terminal_obs).squeeze(-1)
            rewards = rewards.clone()
            rewards[ids] += self.gamma * values * timeouts[ids].to(self.device)
        PPO.process_env_step(self, obs, rewards, dones, extras)

    def update(self) -> dict:
        loss_dict = super().update()
        if self.ball_aux_optimizer is not None:
            loss_dict["ball_regression"] = self._update_ball_head()
            loss_dict["aux_action_kl"] = self.aux_kl
            loss_dict.update(self.aux_metrics)
        if self.amp is not None:
            loss_dict["amp"] = self._update_amp()
        return loss_dict

    def _update_ball_head(self) -> float:
        # Statistics are pre-auxiliary-update, once per stored observation, irrespective
        # of acceptance. PPO clear() only resets its write index, not the tensors.
        flat = self.storage.observations.flatten(0, 1)
        metrics = ball_prediction_metrics(self.policy, flat)
        self.aux_metrics = {"ball/" + key: value for key, value in metrics.items()}
        self.aux_kl = 0.0
        accepted = rejected = fallback = attempted = 0
        trial_max = 0.
        encoder = list(self.policy.perception_encoder.parameters())
        params = encoder + list(self.policy.ball_head.parameters())
        monitor = flat[::max(1, len(flat) // 512)][:512]
        with torch.no_grad():
            stage_mu = self.policy.act_inference(monitor).clone()
            std = (self.policy.std if self.policy.noise_std_type == "scalar" else self.policy.log_std.exp()).detach().clamp(min=1.e-6)
        epochs = self.ball_aux_epochs or self.num_learning_epochs
        generator = self.storage.mini_batch_generator(self.num_mini_batches, epochs)
        for obs_batch, *_ in generator:
            attempted += 1
            with torch.no_grad():
                old_mu = self.policy.act_inference(obs_batch).clone()
            saved_params = [p.detach().clone() for p in params]
            saved_optimizer = copy.deepcopy(self.ball_aux_optimizer.state_dict())
            base_lr = self.ball_aux_optimizer.param_groups[0]["lr"]

            def restore():
                with torch.no_grad():
                    for p, saved in zip(params, saved_params):
                        p.copy_(saved)
                self.ball_aux_optimizer.load_state_dict(saved_optimizer)

            succeeded = False
            for trial in range(7 if self.ball_aux_backtracking else 1):
                if trial:
                    restore()
                for group in self.ball_aux_optimizer.param_groups:
                    group["lr"] = base_lr * (.25 ** trial)
                self.ball_aux_optimizer.zero_grad(set_to_none=True)
                loss = F.mse_loss(self.policy.predict_ball_state(obs_batch), obs_batch[self.policy.privileged_group])
                (self.ball_aux_coef * loss).backward()
                torch.nn.utils.clip_grad_norm_(params, self.max_grad_norm, error_if_nonfinite=True)
                self.ball_aux_optimizer.step()
                with torch.no_grad():
                    kl = (.5 * ((self.policy.act_inference(obs_batch) - old_mu) / std).square().sum(-1)).mean().item()
                    stage_kl = (.5 * ((self.policy.act_inference(monitor) - stage_mu) / std).square().sum(-1)).mean().item()
                trial_max = max(trial_max, kl)
                finite = torch.isfinite(torch.tensor([kl, stage_kl])).all().item()
                # Also limit cumulative drift on a fixed, explicitly sampled monitor batch.
                if finite and kl <= self.ball_aux_max_kl and (not self.ball_aux_backtracking or stage_kl <= self.ball_aux_max_kl):
                    self.aux_kl = max(self.aux_kl, kl)
                    accepted += 1
                    succeeded = True
                    break
                rejected += 1
            if not succeeded:
                restore()
                if not self.ball_aux_backtracking:
                    break
                # Keep learning the head without Adam momentum moving the encoder.
                self.ball_aux_optimizer.zero_grad(set_to_none=True)
                loss = F.mse_loss(self.policy.predict_ball_state(obs_batch), obs_batch[self.policy.privileged_group])
                (self.ball_aux_coef * loss).backward()
                for p in encoder:
                    p.grad = None
                torch.nn.utils.clip_grad_norm_(self.policy.ball_head.parameters(), self.max_grad_norm, error_if_nonfinite=True)
                self.ball_aux_optimizer.step()
                fallback += 1
            # Trial LR is local; next batch can again attempt a useful encoder step.
            for group in self.ball_aux_optimizer.param_groups:
                group["lr"] = base_lr
        with torch.no_grad():
            stage_kl = (.5 * ((self.policy.act_inference(monitor) - stage_mu) / std).square().sum(-1)).mean().item()
        self.aux_metrics.update({"aux/attempted_batches": attempted, "aux/encoder_updates": accepted,
            "aux/rejected_trials": rejected, "aux/head_only_batches": fallback,
            "aux/trial_max_kl": trial_max, "aux/stage_monitor_kl": stage_kl,
            "aux/monitor_count": len(monitor), "aux/base_lr": self.ball_aux_optimizer.param_groups[0]["lr"]})
        return metrics["mse"]

    def _update_amp(self) -> float:
        mean_loss = 0.0
        num_updates = 0
        generator = self.storage.mini_batch_generator(self.num_mini_batches, self.num_learning_epochs)
        for obs_batch, *_ in generator:
            policy_obs = obs_batch[self.amp_obs_group]
            expert_obs = self.motion_library.sample_expert_amp_obs(policy_obs.shape[0])
            loss, _, _ = self.amp.compute_loss(policy_obs, expert_obs)

            self.amp_optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.amp.parameters(), 10.0, error_if_nonfinite=True)
            self.amp_optimizer.step()

            mean_loss += loss.item()
            num_updates += 1
        return mean_loss / max(num_updates, 1)


class SkillAMPPPO(BallRegressionPPO):
    """`BallRegressionPPO` with one AMP discriminator and one critic per skill (the v11 recipe).

    The env routes every transition to a skill -- left-foot or right-foot -- from the ball's
    lateral position (see `mdp.kickball_state`), and publishes that routing as a one-hot gating
    vector in its own observation group. This class uses that vector for the two things the
    recipe says use it:

    - **Style reward**: the discriminator for the routed skill scores the motion window, so the
      reward only pays for a swing that matches the side the ball is on. The mixing follows the
      recipe exactly: `amp_reward = discriminator_reward * amp_reward_scale`, then
      `reward = amp_reward * amp_coef + task_reward * (1 - amp_coef)`, giving AMP an effective
      weight of `0.5 * 0.30` against the task reward's `0.70` at the default settings.
    - **Value function**: `PerceptionActorCritic.evaluate` returns the routed critic's value, so
      GAE, the timeout bootstrap and the value loss all follow the same gating without any of
      them needing to know skills exist.

    The discriminators get their own optimizer with the recipe's weight decay (`1e-3` on the
    trunks, `1e-1` on the output layers). Their gradients are clipped independently at norm 10.
    """

    def __init__(
        self,
        policy,
        *args,
        num_skills: int = 2,
        skill_obs_group: str = "skill",
        amp_trunk_weight_decay: float = 1.0e-3,
        amp_head_weight_decay: float = 1.0e-1,
        **kwargs,
    ):
        super().__init__(policy, *args, **kwargs)
        self.num_skills = num_skills
        self.skill_obs_group = skill_obs_group
        self.amp_trunk_weight_decay = amp_trunk_weight_decay
        self.amp_head_weight_decay = amp_head_weight_decay

    def init_storage(self, training_type, num_envs, num_transitions_per_env, obs, actions_shape):
        # PPO's own storage is exactly right here: the reward is a single mixed scalar and the
        # value is already skill-selected by the policy, so nothing about the buffer is per-skill
        PPO.init_storage(self, training_type, num_envs, num_transitions_per_env, obs, actions_shape)
        if self.policy.num_critics != self.num_skills:
            raise ValueError(
                f"one critic per skill: num_skills={self.num_skills} but the policy has"
                f" num_critics={self.policy.num_critics}"
            )
        if self.motion_library is not None and self.amp is None:
            if self.motion_library.num_clips != self.num_skills:
                raise ValueError(
                    f"num_skills={self.num_skills} but the motion library holds"
                    f" {self.motion_library.num_clips} clips -- skill k is trained on clip k, so"
                    " they have to match"
                )
            self.amp = SkillAMP(
                num_obs=obs[self.amp_obs_group].shape[-1], num_skills=self.num_skills
            ).to(self.device)
            self.amp.set_statistics(self.motion_library.sample_expert_amp_obs(2048))
            self.amp_optimizer = torch.optim.Adam(
                [
                    {"params": self.amp.trunk_parameters(), "weight_decay": self.amp_trunk_weight_decay},
                    {"params": self.amp.head_parameters(), "weight_decay": self.amp_head_weight_decay},
                ],
                lr=self.amp_lr,
            )

    def _skill_ids(self, obs) -> torch.Tensor:
        """Per-env skill index from the env's one-hot gating vector."""
        return obs[self.skill_obs_group].argmax(dim=-1)

    def _score_amp(self, amp_obs, obs):
        return self.amp.predict_reward(amp_obs, self._skill_ids(obs))

    def _update_amp(self) -> float:
        """Train each discriminator against its own clip, on the transitions routed to it."""
        mean_loss = 0.0
        num_updates = 0
        generator = self.storage.mini_batch_generator(self.num_mini_batches, self.num_learning_epochs)
        for obs_batch, *_ in generator:
            policy_obs = obs_batch[self.amp_obs_group]
            skill_ids = self._skill_ids(obs_batch)

            loss = None
            for skill in range(self.num_skills):
                skill_policy_obs = policy_obs[skill_ids == skill]
                if skill_policy_obs.shape[0] == 0:
                    continue
                # one expert window per policy sample, so a skill that was rarely routed to this
                # batch also gets a proportionally small gradient rather than being drowned out
                # by a fixed-size expert batch
                expert_obs = self.motion_library.sample_expert_amp_obs(
                    skill_policy_obs.shape[0], clip_id=skill
                )
                skill_loss, _, _ = self.amp.compute_skill_loss(skill_policy_obs, expert_obs, skill)
                skill_loss = skill_loss * (skill_policy_obs.shape[0] / policy_obs.shape[0])
                loss = skill_loss if loss is None else loss + skill_loss
            if loss is None:
                continue

            self.amp_optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.amp.parameters(), 10.0, error_if_nonfinite=True)
            self.amp_optimizer.step()

            mean_loss += loss.item()
            num_updates += 1
        return mean_loss / max(num_updates, 1)
