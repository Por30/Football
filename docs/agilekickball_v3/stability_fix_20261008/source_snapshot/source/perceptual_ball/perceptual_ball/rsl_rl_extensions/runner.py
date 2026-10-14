# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch
import warnings
import hashlib
from pathlib import Path

from rsl_rl.algorithms import PPO
from rsl_rl.modules import ActorCritic, ActorCriticRecurrent, resolve_rnd_config, resolve_symmetry_config
from rsl_rl.runners import OnPolicyRunner

from .algorithm import BallRegressionPPO, SkillAMPPPO  # noqa: F401
from .modules import PerceptionActorCritic  # noqa: F401
from .contact_outcome import ContactOutcomePPO, OutcomeActorCritic  # noqa: F401
from .state_feedback import StateFeedbackPPO, StateFeedbackActorCritic  # noqa: F401


class BallRegressionOnPolicyRunner(OnPolicyRunner):
    """`OnPolicyRunner` that can resolve `PerceptionActorCritic`/`BallRegressionPPO` by name, and
    that loads the AMP reference-motion library for `BallRegressionPPO`.

    rsl-rl-lib's own `_construct_algorithm` resolves `policy.class_name`/`algorithm.class_name`
    via a bare `eval()` against `on_policy_runner.py`'s module globals, so it can only ever see
    rsl_rl's own classes (`ActorCritic`, `ActorCriticRecurrent`, `PPO`). Overriding it here --
    same body, just defined in a module that also imports the extra classes -- is the standard,
    non-forking way to plug in a custom network/algorithm without patching the installed
    rsl-rl-lib package itself.

    `MotionLibrary` is constructed here (not threaded through `RslRlPpoAlgorithmCfg`, which is a
    strongly-typed dataclass with no field for it) and passed to `BallRegressionPPO` directly.
    """

    def _construct_algorithm(self, obs) -> PPO:
        self.alg_cfg = resolve_rnd_config(self.alg_cfg, obs, self.cfg["obs_groups"], self.env)
        self.alg_cfg = resolve_symmetry_config(self.alg_cfg, self.env)

        actor_critic_class = eval(self.policy_cfg.pop("class_name"))
        actor_critic: ActorCritic | ActorCriticRecurrent = actor_critic_class(
            obs, self.cfg["obs_groups"], self.env.num_actions, **self.policy_cfg
        ).to(self.device)

        alg_class = eval(self.alg_cfg.pop("class_name"))
        motion_library = None
        if issubclass(alg_class, BallRegressionPPO):
            from ..tasks.manager_based.perceptual_ball.mdp.amp import KICK_MOTION_CLIP_PATHS, MotionLibrary

            motion_library = MotionLibrary(KICK_MOTION_CLIP_PATHS, device=self.device)
        alg: PPO = alg_class(
            actor_critic, device=self.device, motion_library=motion_library, **self.alg_cfg,
            multi_gpu_cfg=self.multi_gpu_cfg,
        )

        alg.init_storage("rl", self.env.num_envs, self.num_steps_per_env, obs, [self.env.num_actions])
        return alg

    def save(self, path: str, infos=None):
        state = {
            "model_state_dict": self.alg.policy.state_dict(),
            "optimizer_state_dict": self.alg.optimizer.state_dict(),
            "iter": self.current_learning_iteration, "infos": infos,
            "soccer_schema_version": 3,
            "amp_state_dict": self.alg.amp.state_dict() if self.alg.amp is not None else None,
            "amp_optimizer_state_dict": self.alg.amp_optimizer.state_dict() if self.alg.amp is not None else None,
            "ball_aux_optimizer_state_dict": self.alg.ball_aux_optimizer.state_dict() if self.alg.ball_aux_optimizer else None,
            "torch_rng_state": torch.get_rng_state(),
        }
        if hasattr(self.alg, "outcome_config"):
            state["contact_outcome"] = {
                "config": self.alg.outcome_config,
                "optimizer": self.alg.outcome_optimizer.state_dict() if self.alg.outcome_optimizer else None,
            }
        if hasattr(self.alg, "state_feedback_config"):
            state['state_feedback'] = {'config': self.alg.state_feedback_config,
                                       'aux_updates': self.alg.state_feedback_updates}
        kb = getattr(getattr(getattr(self, "env", None), "unwrapped", None), "_kickball", None)
        if hasattr(kb, "curriculum_state_dict"):
            state[getattr(kb, "curriculum_checkpoint_key", "agile_success_curriculum")] = kb.curriculum_state_dict()
        if hasattr(kb, "exposure_steps"):
            state["agile_incoming_exposure_steps"] = kb.exposure_steps
        if self.alg.rnd:
            state["rnd_state_dict"] = self.alg.rnd.state_dict()
            state["rnd_optimizer_state_dict"] = self.alg.rnd_optimizer.state_dict()
        if hasattr(self, 'warm_start_info'):
            state['initialization'] = self.warm_start_info
        torch.save(state, path)
        if getattr(self, "logger_type", None) in ["neptune", "wandb"] and not self.disable_logs:
            self.writer.save_model(path, self.current_learning_iteration)

    def warm_start_from_v2(self, path):
        """Explicit weight initialization, never a PPO/curriculum/optimizer resume."""
        if (not isinstance(self.alg, StateFeedbackPPO) or self.current_learning_iteration != 0
                or self.alg.state_feedback_updates != 0 or self.alg.optimizer.state
                or self.alg.ball_aux_optimizer.state
                or (self.alg.amp is not None and self.alg.amp_optimizer.state)):
            raise ValueError('v2 warm-start requires a fresh state feedback runner')
        path = Path(path).expanduser().resolve()
        state = torch.load(path, map_location=self.device, weights_only=False)
        course = state.get('agile_v2_recovery_curriculum', {})
        if (state.get('soccer_schema_version') != 3 or course.get('schema') != 5
                or course.get('config', {}).get('revision') != 'v1_speed_only_20260925'
                or 'state_feedback' in state or 'contact_outcome' in state):
            raise ValueError('v2 warm-start source must be the compatible v2 baseline')
        source = state['model_state_dict']
        target = self.alg.policy.state_dict()
        mapped = {}
        for key, value in target.items():
            if key.startswith(('ball_head.', 'actor.residual.')) or key == 'ball_state_scale':
                continue
            old_key = 'actor.' + key[len('actor.base.'):] if key.startswith('actor.base.') else key
            if (old_key not in source or source[old_key].shape != value.shape
                    or not torch.isfinite(source[old_key]).all()):
                raise ValueError('v2 warm-start incompatible/nonfinite weight: ' + old_key)
            mapped[key] = source[old_key]
        if not all(torch.isfinite(v).all() for v in source.values()):
            raise ValueError('v2 warm-start source contains nonfinite weights')
        if (self.alg.policy.actor.residual[-1].weight.count_nonzero()
                or self.alg.policy.actor.residual[-1].bias.count_nonzero()):
            raise ValueError('v2 warm-start requires initially zero action correction')
        amp_state = state.get('amp_state_dict')
        if self.alg.amp is not None:
            expected = self.alg.amp.state_dict()
            if (not isinstance(amp_state, dict) or set(amp_state) != set(expected)
                    or any(amp_state[k].shape != v.shape or not torch.isfinite(amp_state[k]).all()
                           for k, v in expected.items())):
                raise ValueError('v2 warm-start incompatible/nonfinite AMP state')
        target.update(mapped)
        self.alg.policy.load_state_dict(target, strict=True)
        if self.alg.amp is not None:
            self.alg.amp.load_state_dict(amp_state, strict=True)
        self.warm_start_info = dict(schema=1, kind='v2_weights_only', source=str(path),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(), source_iteration=state['iter'],
            transferred=['main_actor', 'perception_encoder', 'critic_and_normalization', 'action_std', 'AMP'],
            fresh=['PPO_optimizer', 'ball_aux_optimizer', 'AMP_optimizer', 'ball_head', 'residual', 'curriculum', 'iteration_counter'])
        print('[INFO] v2 warm-start weights loaded; optimizers/curriculum/iteration are fresh: ' + str(path), flush=True)

    def load(self, path, load_optimizer=True, map_location=None, allow_legacy=False):
        state = torch.load(path, weights_only=False, map_location=map_location or self.device)
        if state.get("soccer_schema_version") != 3:
            if load_optimizer and not allow_legacy:
                raise ValueError("Legacy checkpoint lacks corrected AMP training state; use an explicit warm start")
            warnings.warn("Legacy policy warm start: AMP and auxiliary optimizer are freshly initialized", stacklevel=2)
        kb = getattr(getattr(getattr(self, "env", None), "unwrapped", None), "_kickball", None)
        course_key = getattr(kb, "curriculum_checkpoint_key", "agile_success_curriculum")
        if course_key == "agile_speed_curriculum" and "agile_success_curriculum" in state:
            raise ValueError("Old strict-success v1 checkpoint is incompatible with the new speed curriculum; "
                             "start a fresh training run (no --resume).")
        if hasattr(kb, "validate_curriculum_state_dict"):
            kb.validate_curriculum_state_dict(state.get(course_key))
        # Preflight before super().load mutates model/PPO state. V2 has no outcome stage.
        outcome = state.get("contact_outcome")
        if hasattr(self.alg, "outcome_config"):
            if not isinstance(outcome, dict) or outcome.get("config") != self.alg.outcome_config:
                raise ValueError("Incompatible contact outcome config; start fresh without --resume")
            if load_optimizer and self.alg.outcome_optimizer is not None:
                saved_optimizer = outcome.get("optimizer")
                if not isinstance(saved_optimizer, dict) or not {"state", "param_groups"} <= saved_optimizer.keys():
                    raise ValueError("Checkpoint has no valid contact outcome optimizer state")
        elif outcome is not None:
            raise ValueError("Contact outcome checkpoint requires its v3 algorithm")
        feedback = state.get('state_feedback')
        if hasattr(self.alg, 'state_feedback_config'):
            if (not isinstance(feedback, dict)
                    or feedback.get('config') != self.alg.state_feedback_config
                    or type(feedback.get('aux_updates')) is not int or feedback['aux_updates'] < 0):
                raise ValueError('Incompatible state feedback checkpoint config/counter')
            if load_optimizer:
                optimizer = state.get('ball_aux_optimizer_state_dict')
                expected = self.alg.ball_aux_optimizer.state_dict()['param_groups']
                if (not isinstance(optimizer, dict) or not isinstance(optimizer.get('state'), dict)
                        or not isinstance(optimizer.get('param_groups'), list)
                        or len(optimizer['param_groups']) != len(expected)
                        or any(len(group.get('params', [])) != len(target['params'])
                               for group, target in zip(optimizer['param_groups'], expected))):
                    raise ValueError('Missing or incompatible state feedback auxiliary optimizer')
        elif feedback is not None:
            raise ValueError('State feedback checkpoint requires its v3 algorithm')
        infos = super().load(path, load_optimizer=load_optimizer, map_location=map_location or self.device)
        if 'initialization' in state:
            self.warm_start_info = state['initialization']
        if hasattr(self.alg, 'state_feedback_config'):
            self.alg.state_feedback_updates = feedback['aux_updates']
        if hasattr(self.alg, "outcome_config") and load_optimizer and self.alg.outcome_optimizer is not None:
            self.alg.outcome_optimizer.load_state_dict(outcome["optimizer"])
        if state.get("soccer_schema_version") == 3:
            if self.alg.amp is not None:
                if state["amp_state_dict"] is None:
                    raise ValueError("Checkpoint has no AMP state for this task")
                self.alg.amp.load_state_dict(state["amp_state_dict"])
                if load_optimizer:
                    self.alg.amp_optimizer.load_state_dict(state["amp_optimizer_state_dict"])
            if load_optimizer and self.alg.ball_aux_optimizer:
                if state["ball_aux_optimizer_state_dict"] is None:
                    raise ValueError("Checkpoint has no auxiliary optimizer state")
                self.alg.ball_aux_optimizer.load_state_dict(state["ball_aux_optimizer_state_dict"])
            if load_optimizer:
                torch.set_rng_state(state["torch_rng_state"].cpu())
        kb = getattr(getattr(getattr(self, "env", None), "unwrapped", None), "_kickball", None)
        # Restore versioned v1 course state, including frozen play distribution.
        if hasattr(kb, "load_curriculum_state_dict"):
            course_state = state.get(course_key)
            if course_state is None and course_key == "agile_speed_curriculum":
                # A v0 checkpoint has only an averaged exposure scalar, not strict windows.
                course_state = dict(schema=2, config=kb.course_config,
                                    exposure_steps=state.get("agile_incoming_exposure_steps", 0.))
            kb.load_curriculum_state_dict(course_state)
            kb.curriculum_training = bool(load_optimizer)
        # Environment distribution belongs to the checkpoint, also during inference.
        elif hasattr(kb, "exposure_steps"):
            kb.exposure_offset = float(state.get("agile_incoming_exposure_steps", 0.))
            kb.incoming_steps.zero_()
            from ..tasks.manager_based.perceptual_ball.mdp.agilekickball import exposure_speed_curriculum
            exposure_speed_curriculum(self.env.unwrapped, None)
        return infos
