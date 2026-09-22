# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import Articulation
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils.math import wrap_to_pi

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def joint_pos_target_l2(env: ManagerBasedRLEnv, target: float, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """Penalize joint position deviation from a target value."""
    # extract the used quantities (to enable type-hinting)
    asset: Articulation = env.scene[asset_cfg.name]
    # wrap the joint positions to (-pi, pi)
    joint_pos = wrap_to_pi(asset.data.joint_pos[:, asset_cfg.joint_ids])
    # compute the reward
    return torch.sum(torch.square(joint_pos - target), dim=1)


##
# Kickball task reward terms, adapted from the x2_kickball_depth_v3 handoff recipe
# (/home/cao/perceptual_ball/kickball). All read the shared per-env state machine on
# `env._kickball` (see mdp/kickball_state.py), which is advanced once per step by the
# zero-weight `tick_kickball_state` reward term declared first in RewardsCfg.
##


def stand_task(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    target_height: float = 0.74,
    pos_sigma: float = 0.3,
    vel_sigma: float = 0.5,
    upright_sigma: float = 0.2,
    height_sigma: float = 0.1,
) -> torch.Tensor:
    """Average of four exponential rewards: stay near the anchor, stay still, stay upright,
    keep the default standing height. The handoff doc names these four terms but doesn't spell
    out their exact formulas/scales, so the sigmas here are a reasonable choice, not a verbatim
    port -- easy to retune once training results are in.
    """
    robot = env.scene[robot_cfg.name]
    kb = env._kickball

    pos_err = torch.norm(robot.data.root_pos_w[:, :2] - kb.anchor_xy, dim=-1)
    anchor_reward = torch.exp(-(pos_err**2) / pos_sigma**2)

    vel_err = torch.norm(robot.data.root_lin_vel_w[:, :2], dim=-1)
    vel_reward = torch.exp(-(vel_err**2) / vel_sigma**2)

    upright_err = torch.norm(robot.data.projected_gravity_b[:, :2], dim=-1)
    upright_reward = torch.exp(-(upright_err**2) / upright_sigma**2)

    height_err = robot.data.root_pos_w[:, 2] - target_height
    height_reward = torch.exp(-(height_err**2) / height_sigma**2)

    return (anchor_reward + vel_reward + upright_reward + height_reward) / 4.0


def face_ball_task(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    ball_cfg: SceneEntityCfg = SceneEntityCfg("ball"),
) -> torch.Tensor:
    """`exp(-|yaw_error|) * ball_active`: reward facing the ball while it's in play."""
    robot = env.scene[robot_cfg.name]
    ball = env.scene[ball_cfg.name]
    kb = env._kickball

    to_ball = ball.data.root_pos_w[:, :2] - robot.data.root_pos_w[:, :2]
    bearing = torch.atan2(to_ball[:, 1], to_ball[:, 0])
    w, x, y, z = robot.data.root_quat_w.unbind(-1)
    yaw = torch.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    yaw_error = wrap_to_pi(bearing - yaw)

    return torch.exp(-torch.abs(yaw_error)) * kb.ball_active.float()


def kick_approach_task(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    ball_cfg: SceneEntityCfg = SceneEntityCfg("ball"),
    foot_cfg: SceneEntityCfg = SceneEntityCfg("robot", body_names=".*_ankle_roll_link"),
    dist_threshold: float = 1.6,
) -> torch.Tensor:
    """`exp(-4*min_foot_ball_dist)` while the ball hasn't been kicked yet and is within range."""
    robot = env.scene[robot_cfg.name]
    ball = env.scene[ball_cfg.name]
    kb = env._kickball

    foot_xy = robot.data.body_link_pos_w[:, foot_cfg.body_ids, :2]
    ball_xy = ball.data.root_pos_w[:, :2].unsqueeze(1)
    min_foot_ball_dist = torch.norm(foot_xy - ball_xy, dim=-1).min(dim=1).values

    active = kb.ball_active & (~kb.ball_kicked) & (min_foot_ball_dist < dist_threshold)
    return torch.exp(-4.0 * min_foot_ball_dist) * active.float()


def kick_return_task(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    ball_cfg: SceneEntityCfg = SceneEntityCfg("ball"),
    dist_threshold: float = 2.0,
) -> torch.Tensor:
    """`clamp(ball_return_speed, 0, 3) / 3` while the ball is close and in play."""
    robot = env.scene[robot_cfg.name]
    ball = env.scene[ball_cfg.name]
    kb = env._kickball

    dist = torch.norm(ball.data.root_pos_w[:, :2] - robot.data.root_pos_w[:, :2], dim=-1)
    active = kb.ball_active & (dist < dist_threshold)
    return torch.clamp(kb.ball_return_speed, min=0.0, max=3.0) / 3.0 * active.float()


def kick_bonus(env: ManagerBasedRLEnv) -> torch.Tensor:
    """One-time bonus the step a kick is detected as successful."""
    return env._kickball.kick_success_flag.float()


def miss_penalty(env: ManagerBasedRLEnv) -> torch.Tensor:
    """One-time penalty the step the ball rolls past/away/to a stop without being kicked."""
    return env._kickball.just_missed.float()
