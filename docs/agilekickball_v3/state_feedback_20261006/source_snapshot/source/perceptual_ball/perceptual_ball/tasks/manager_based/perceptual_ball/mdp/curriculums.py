# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING
import math

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def ramp_ball_speed_target(
    env: ManagerBasedRLEnv,
    env_ids,
    data: float,
    start_speed: float,
    end_speed: float,
    ramp_steps: int,
) -> float:
    """Linearly ramp a reward term's speed target from `start_speed` to `end_speed`.

    Used with `mdp.modify_term_cfg` on `rewards.ball_speed_away.params.max_speed`: since that
    reward clamps at `max_speed`, a low cap means even a slow nudge already saturates the
    reward, so the robot first learns to kick the ball at all before the cap is raised and it
    has to kick harder for the same reward.
    """
    progress = min(env.common_step_counter / ramp_steps, 1.0)
    return start_speed + progress * (end_speed - start_speed)


def ramp_incoming_ball_speed(
    env: ManagerBasedRLEnv,
    env_ids,
    min_speed: float = 0.4,
    initial_max_speed: float = 0.8,
    final_max_speed: float = 2.0,
    ramp_steps: int = 240_000,
    start_step: int = 0,
) -> float:
    """Reset-time curriculum for future serves, in m/s and global control steps.

    The lower bound stays fixed to retain easy examples. Existing balls are untouched.
    `start_step` restores curriculum progress explicitly when resuming or evaluating;
    environment common_step_counter starts at zero in a new process.
    """
    if not all(math.isfinite(v) for v in (min_speed, initial_max_speed, final_max_speed)):
        raise ValueError("Serve speed bounds must be finite")
    if not 0 < min_speed <= initial_max_speed <= final_max_speed:
        raise ValueError("Require 0 < min_speed <= initial_max_speed <= final_max_speed")
    if isinstance(ramp_steps, bool) or not isinstance(ramp_steps, int) or ramp_steps <= 0:
        raise ValueError("ramp_steps must be a positive integer")
    if isinstance(start_step, bool) or not isinstance(start_step, int) or start_step < 0:
        raise ValueError("start_step must be a nonnegative integer")
    progress = min(max((env.common_step_counter + start_step) / ramp_steps, 0.0), 1.0)
    upper = initial_max_speed + progress * (final_max_speed - initial_max_speed)
    env._kickball.serve_speed_range = (min_speed, upper)
    return upper
