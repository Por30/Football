# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch
import warnings

from rsl_rl.algorithms import PPO
from rsl_rl.modules import ActorCritic, ActorCriticRecurrent, resolve_rnd_config, resolve_symmetry_config
from rsl_rl.runners import OnPolicyRunner

from .algorithm import BallRegressionPPO, SkillAMPPPO  # noqa: F401
from .modules import PerceptionActorCritic  # noqa: F401


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
        kb = getattr(getattr(getattr(self, "env", None), "unwrapped", None), "_kickball", None)
        if hasattr(kb, "curriculum_state_dict"):
            state[getattr(kb, "curriculum_checkpoint_key", "agile_success_curriculum")] = kb.curriculum_state_dict()
        if hasattr(kb, "exposure_steps"):
            state["agile_incoming_exposure_steps"] = kb.exposure_steps
        if self.alg.rnd:
            state["rnd_state_dict"] = self.alg.rnd.state_dict()
            state["rnd_optimizer_state_dict"] = self.alg.rnd_optimizer.state_dict()
        torch.save(state, path)
        if getattr(self, "logger_type", None) in ["neptune", "wandb"] and not self.disable_logs:
            self.writer.save_model(path, self.current_learning_iteration)

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
        infos = super().load(path, load_optimizer=load_optimizer, map_location=map_location or self.device)
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
