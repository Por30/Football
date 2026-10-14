# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import RigidObject
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils.math import quat_apply_inverse, subtract_frame_transforms

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def ball_pos_b(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    ball_cfg: SceneEntityCfg = SceneEntityCfg("ball"),
) -> torch.Tensor:
    """The ball's position in the robot's root frame. Privileged (critic-only) observation."""
    robot = env.scene[robot_cfg.name]
    ball: RigidObject = env.scene[ball_cfg.name]
    ball_pos_b, _ = subtract_frame_transforms(
        robot.data.root_pos_w, robot.data.root_quat_w, ball.data.root_pos_w[:, :3]
    )
    return ball_pos_b


def ball_lin_vel_b(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    ball_cfg: SceneEntityCfg = SceneEntityCfg("ball"),
) -> torch.Tensor:
    """The ball's linear velocity in the robot's root frame. Privileged (critic-only) observation."""
    robot = env.scene[robot_cfg.name]
    ball: RigidObject = env.scene[ball_cfg.name]
    return quat_apply_inverse(robot.data.root_quat_w, ball.data.root_lin_vel_w)


def body_pos_in_root_frame(asset, body_ids: list[int]) -> torch.Tensor:
    """Positions of `body_ids` in `asset`'s own root frame, flattened to (N, len(body_ids)*3).

    Shared by `end_effector_pos_b` below and `mdp.amp.amp_features`'s end-effector
    feature, so the two stay in the same convention.
    """
    num_bodies = len(body_ids)
    num_envs = asset.data.root_pos_w.shape[0]
    body_pos_w = asset.data.body_link_pos_w[:, body_ids, :]
    root_pos_exp = asset.data.root_pos_w.unsqueeze(1).expand(-1, num_bodies, -1).reshape(-1, 3)
    root_quat_exp = asset.data.root_quat_w.unsqueeze(1).expand(-1, num_bodies, -1).reshape(-1, 4)
    body_pos_b, _ = subtract_frame_transforms(root_pos_exp, root_quat_exp, body_pos_w.reshape(-1, 3))
    return body_pos_b.reshape(num_envs, num_bodies * 3)


def end_effector_pos_b(
    env: ManagerBasedRLEnv,
    asset_cfg: SceneEntityCfg = SceneEntityCfg(
        "robot", body_names=["left_palm_link", "right_palm_link", "left_ankle_pitch_link", "right_ankle_pitch_link", "head_link"]
    ),
) -> torch.Tensor:
    """The five tracked end-effectors' positions in the robot's own root frame (proprioceptive:
    this is regular forward-kinematics info, not a privileged ball-state leak)."""
    robot = env.scene[asset_cfg.name]
    return body_pos_in_root_frame(robot, asset_cfg.body_ids)


def skill_gating_weights(env: ManagerBasedRLEnv) -> torch.Tensor:
    """One-hot `[kick_left, kick_right]` gating weights for the currently routed skill.

    This is *not* an actor input -- the v11 spec keeps the kicking side out of the policy's
    observation entirely. It is published as its own observation group only so the training side
    can read it off the rollout buffer by name (the same way it reads the `amp` group) to pick
    which AMP discriminator grades each transition and which critic values it.
    """
    state = getattr(env, "_kickball", None)
    if state is None:
        # `ObservationManager.__init__` calls every term once to measure its shape, before the
        # env applies its startup events -- i.e. before the state machine is attached.
        return torch.zeros(env.num_envs, 2, device=env.device)
    return torch.nn.functional.one_hot(state.skill_ids, num_classes=2).float()
