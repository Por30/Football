# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Project-specific event terms (Isaac Lab's own `isaaclab.envs.mdp.events` has no equivalent)."""

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import Articulation
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils.math import sample_uniform

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedEnv


def randomize_default_joint_pos(
    env: ManagerBasedEnv,
    env_ids: torch.Tensor | None,
    offset_range: tuple[float, float],
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> None:
    """Startup event: give each robot a small fixed offset on every joint's default position.

    This is a joint-calibration error, not per-episode noise: `default_joint_pos` is the zero
    point of the position-action offset, the reference the `joint_pos_rel` observation is
    measured against, and the pose every reset writes. Perturbing it once at startup means each
    robot lives with a slightly different idea of "straight" for the whole run, which is what a
    real fleet looks like; re-drawing it per episode would instead just add noise the policy can
    average away.
    """
    asset: Articulation = env.scene[asset_cfg.name]
    if env_ids is None:
        env_ids = torch.arange(env.num_envs, device=asset.data.default_joint_pos.device)
    offsets = sample_uniform(
        offset_range[0],
        offset_range[1],
        (len(env_ids), asset.data.default_joint_pos.shape[1]),
        asset.data.default_joint_pos.device,
    )
    asset.data.default_joint_pos[env_ids] += offsets

    # Actions are constructed before startup events and hold a cloned offset.
    action = env.action_manager.get_term("joint_pos")
    action._offset[env_ids] = asset.data.default_joint_pos[env_ids][:, action._joint_ids]
