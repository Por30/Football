# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def roll_pitch_exceeded(
    env: ManagerBasedRLEnv,
    roll_limit: float,
    pitch_limit: float,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Terminate when the robot has tipped past separate roll/pitch limits."""
    robot = env.scene[asset_cfg.name]
    w, x, y, z = robot.data.root_quat_w.unbind(-1)
    roll = torch.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    pitch = torch.asin(torch.clamp(2.0 * (w * y - z * x), -1.0, 1.0))
    return (roll.abs() > roll_limit) | (pitch.abs() > pitch_limit)


def walked_away_from_anchor(
    env: ManagerBasedRLEnv, max_dist: float, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")
) -> torch.Tensor:
    """Terminate when the robot's root has drifted too far from its recorded stand anchor."""
    robot = env.scene[asset_cfg.name]
    dist = torch.norm(robot.data.root_pos_w[:, :2] - env._kickball.anchor_xy, dim=-1)  # type: ignore[attr-defined]
    return dist > max_dist


def fail_on_non_finite_state(
    env: ManagerBasedRLEnv,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    ball_cfg: SceneEntityCfg = SceneEntityCfg("ball"),
) -> torch.Tensor:
    """Raise the moment the action or the simulated state goes non-finite, naming what broke.

    This never terminates an episode: a NaN here has already poisoned every PPO gradient that
    follows it, so the run is over either way -- the point is to stop at the step it happened
    instead of hours of flat curves later.

    It checks the state rather than the observation groups on purpose. Every observation in this
    task (proprioception, the synthetic depth image, the AMP features, the privileged ball state)
    is a pure function of the robot state, the ball state and the last action, so this catches the
    same blowups; reading `observation_manager.compute()` here would instead rebuild the depth
    image a second time every step to learn it.
    """
    robot: Articulation = env.scene[asset_cfg.name]
    ball: RigidObject = env.scene[ball_cfg.name]
    checks = (
        ("action", env.action_manager.action),
        ("robot root state", robot.data.root_state_w),
        ("robot joint pos", robot.data.joint_pos),
        ("robot joint vel", robot.data.joint_vel),
        ("ball root state", ball.data.root_state_w),
    )
    # one stacked reduction, so the (unavoidable) device sync below happens once per step
    finite = torch.stack([torch.isfinite(tensor.reshape(env.num_envs, -1)).all(dim=-1) for _, tensor in checks])
    if bool(finite.all()):
        return torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)

    for (name, _), term_finite in zip(checks, finite.unbind()):
        bad_env_ids = (~term_finite).nonzero(as_tuple=False).squeeze(-1)
        if len(bad_env_ids) > 0:
            raise FloatingPointError(
                f"{name} is NaN/Inf in {len(bad_env_ids)} env(s) at step {env.common_step_counter}"
                f" (first ids: {bad_env_ids[:8].tolist()})"
            )
    return torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)


def self_collision(
    env: ManagerBasedRLEnv,
    body_pairs: list[tuple[str, str, float]],
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Terminate when any named body pair comes closer than its own distance threshold.

    Pairs are given as (body_a, body_b, min_distance_m) and checked from link positions, so this
    needs no contact sensor on the robot -- it exists to rule out kicks that only work by tangling
    the legs through each other, which the physics solver will let happen at speed.
    """
    robot: Articulation = env.scene[asset_cfg.name]
    body_pos_w = robot.data.body_link_pos_w
    body_names = robot.body_names

    colliding = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
    for name_a, name_b, min_distance in body_pairs:
        idx_a = body_names.index(name_a)
        idx_b = body_names.index(name_b)
        colliding |= torch.norm(body_pos_w[:, idx_a] - body_pos_w[:, idx_b], dim=-1) < min_distance
    return colliding
