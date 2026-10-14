# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""AMP (Adversarial Motion Prior) feature + reference-motion loading.

A discriminator (see `perceptual_ball.rsl_rl_extensions.amp.AMP`) scores whether a window of
robot motion looks like the reference mocap, and that score is mixed into the task reward
(`perceptual_ball.rsl_rl_extensions.algorithm.BallRegressionPPO`). The reference clips are two
real kicking motions retargeted to this exact 29-DOF G1 (`assets/motions/kick/kick_{left,right}.pt`,
produced by replaying /home/cao/PhysHSI/unitree_g1_retarget/*.pkl through this task's own
G1_29DOF_CFG articulation for forward kinematics -- see git history for the one-off preprocessing
script). Per the x2_kickball_depth_v3 handoff doc's own note for this exact situation ("原始mocap
无球轨迹,所以AMP的object三维在expert和policy两侧都用thresh_robot2object=0.0清零"): the raw mocap
carries no ball trajectory, so the object_pos feature below is zeroed on both the expert and the
live (policy) side, rather than mixing in a stale/meaningless ball position.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import torch

from isaaclab.managers import SceneEntityCfg
from isaaclab.utils.math import (
    axis_angle_from_quat,
    matrix_from_quat,
    quat_apply_inverse,
    quat_apply,
    quat_inv,
    quat_mul,
    subtract_frame_transforms,
    yaw_quat,
)

from .observations import body_pos_in_root_frame
from perceptual_ball.amp_features import relative_base_height, pack_amp_frame

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv

# Per-frame AMP feature, matching the x2_kickball_depth_v3 recipe's composition (base_height=1,
# dof_pos=29, end_effector_pos=15 [5 EE x3], base_lin_vel=3, base_ang_vel=3, root_rot_6d=6,
# object_pos=3 = 60 total), over a 10-frame sliding window.
AMP_WINDOW_LENGTH = 10
AMP_OBS_DIM_PER_FRAME = 60

END_EFFECTOR_BODY_NAMES = [
    "left_wrist_roll_link",
    "right_wrist_roll_link",
    "left_ankle_pitch_link",
    "right_ankle_pitch_link",
    "head_link",
]

# .../perceptual_ball/tasks/manager_based/perceptual_ball/mdp/amp.py -> .../perceptual_ball/assets/motions/kick
_MOTIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "assets", "motions", "kick")
KICK_MOTION_CLIP_PATHS = [
    os.path.join(_MOTIONS_DIR, "kick_left.pt"),
    os.path.join(_MOTIONS_DIR, "kick_right.pt"),
]


def amp_features(
    env: ManagerBasedRLEnv,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    ee_cfg: SceneEntityCfg = SceneEntityCfg("robot", body_names=END_EFFECTOR_BODY_NAMES, preserve_order=True),
    ball_cfg: SceneEntityCfg = SceneEntityCfg("ball"),
) -> torch.Tensor:
    """Per-frame AMP feature: base_height, dof_pos, end_effector_pos_b, base_lin_vel_b,
    base_ang_vel_b, root_rot_6d, object_pos (always zero -- see module docstring)."""
    asset = env.scene[asset_cfg.name]

    ee_pos_w = asset.data.body_link_pos_w[:, ee_cfg.body_ids, :]
    base_height = relative_base_height(asset.data.root_pos_w, ee_pos_w)
    ee_pos_b = body_pos_in_root_frame(asset, ee_cfg.body_ids)

    heading_inv = quat_inv(yaw_quat(asset.data.root_quat_w))
    local_rot = quat_mul(heading_inv, asset.data.root_quat_w)
    root_rot_6d = matrix_from_quat(local_rot)[..., :2].reshape(env.num_envs, 6)

    return pack_amp_frame(base_height, asset.data.joint_pos, ee_pos_b,
                          asset.data.root_lin_vel_b, asset.data.root_ang_vel_b, root_rot_6d)


class MotionLibrary:
    """Loads the retargeted kick clips and samples expert AMP-observation windows from them.

    Mirrors the shape of PhysHSI's `motionlib_*.py` (one flat concatenated frame buffer across
    clips, `torch.multinomial` clip sampling, a random-phase start, and a `ratio_random_range`
    playback-speed jitter when resampling from the clip's native fps down to the env's control
    rate) but is self-contained here since there's no shared MotionLib base class to inherit
    from, and this task only has two same-schema clips instead of a whole YAML-driven skill set.
    """

    def __init__(
        self,
        clip_paths: list[str],
        device: str,
        env_fps: float = 50.0,
        ratio_random_range: tuple[float, float] = (0.9, 1.1),
    ):
        self.device = device
        self.env_fps = env_fps
        self.ratio_random_range = ratio_random_range

        clips = [torch.load(p, weights_only=False) for p in clip_paths]
        self.fps = float(clips[0]["fps"])
        self.joint_names = clips[0]["joint_names"]
        for clip in clips:
            if clip["joint_names"] != self.joint_names or abs(float(clip["fps"]) - self.fps) > 1.e-3:
                raise ValueError("AMP clips must share named joint order and fps")
        # clip i is the reference for skill/AMP head i -- KICK_MOTION_CLIP_PATHS is
        # [kick_left, kick_right], the same order as the kick-foot command (see
        # mdp.kickball_state.KICK_FOOT_BODY_NAMES)
        self.num_clips = len(clips)
        lengths = [c["base_position"].shape[0] for c in clips]
        self.lengths = torch.tensor(lengths, device=device)
        ends = torch.cumsum(self.lengths, dim=0)
        self.starts = torch.cat([torch.zeros(1, dtype=torch.long, device=device), ends[:-1]])

        base_position = torch.cat([c["base_position"] for c in clips]).to(device)
        base_quat = torch.cat([c["base_quat"] for c in clips]).to(device)
        joint_position = torch.cat([c["joint_position"] for c in clips]).to(device)
        link_position = torch.cat([c["link_position"] for c in clips]).to(device)  # (N, 5, 3)

        base_lin_vel = torch.zeros_like(base_position)
        base_ang_vel = torch.zeros_like(base_position)
        joint_velocity = torch.zeros_like(joint_position)
        for s, e in zip(self.starts.tolist(), ends.tolist()):
            base_lin_vel[s : e - 1] = (base_position[s + 1 : e] - base_position[s : e - 1]) * self.fps
            base_lin_vel[e - 1] = base_lin_vel[e - 2]
            joint_velocity[s : e - 1] = (joint_position[s + 1 : e] - joint_position[s : e - 1]) * self.fps
            joint_velocity[e - 1] = joint_velocity[e - 2]
            rel_rot = quat_mul(quat_inv(base_quat[s : e - 1]), base_quat[s + 1 : e])
            base_ang_vel[s : e - 1] = axis_angle_from_quat(rel_rot) * self.fps
            base_ang_vel[e - 1] = base_ang_vel[e - 2]

        self.base_height = relative_base_height(base_position, link_position)
        self.base_lin_vel_b = quat_apply_inverse(base_quat, base_lin_vel)
        self.base_ang_vel_b = base_ang_vel  # already expressed in the root's own frame (see above)
        self.joint_position = joint_position
        # kept for RSI (get_motion_state), which needs raw world-frame root state + joint
        # velocities, not the AMP-feature-specific derived quantities above
        self.base_position = base_position
        self.base_quat = base_quat
        self.base_lin_vel_w = base_lin_vel
        self.base_ang_vel_w = quat_apply(base_quat, base_ang_vel)
        self.joint_velocity = joint_velocity

        num_ee = link_position.shape[1]
        root_pos_exp = base_position.unsqueeze(1).expand(-1, num_ee, -1).reshape(-1, 3)
        root_quat_exp = base_quat.unsqueeze(1).expand(-1, num_ee, -1).reshape(-1, 4)
        ee_pos_b, _ = subtract_frame_transforms(root_pos_exp, root_quat_exp, link_position.reshape(-1, 3))
        self.ee_pos_b = ee_pos_b.reshape(base_position.shape[0], num_ee * 3)

        heading_inv = quat_inv(yaw_quat(base_quat))
        local_rot = quat_mul(heading_inv, base_quat)
        self.root_rot_6d = matrix_from_quat(local_rot)[..., :2].reshape(base_position.shape[0], 6)

    def sample_expert_amp_obs(
        self, batch_size: int, window_length: int = AMP_WINDOW_LENGTH, clip_id: int | None = None
    ) -> torch.Tensor:
        """A (batch_size, window_length * AMP_OBS_DIM_PER_FRAME) batch of real reference windows,
        feature-for-feature matching `amp_features`'s per-frame layout (with
        object_pos zeroed, exactly like the live feature -- see module docstring).

        `clip_id` restricts the batch to a single reference clip, which is what a per-skill AMP
        head needs: head 0 must only ever be shown left-foot kicks and head 1 only right-foot
        ones, otherwise both heads learn the same "looks like a kick" score and the style reward
        stops distinguishing the two skills. The default samples across all clips, weighted by
        length, which is what the single-discriminator v3 task wants.
        """
        device = self.device
        if clip_id is None:
            clip_ids = torch.multinomial(self.lengths.float(), batch_size, replacement=True)
        else:
            clip_ids = torch.full((batch_size,), clip_id, device=device, dtype=torch.long)
        starts = self.starts[clip_ids]
        lengths = self.lengths[clip_ids].float()

        ratio = (self.fps / self.env_fps) * (
            torch.rand(batch_size, device=device) * (self.ratio_random_range[1] - self.ratio_random_range[0])
            + self.ratio_random_range[0]
        )
        max_native_start = (lengths - 1 - (window_length - 1) * ratio).clamp(min=0)
        phase = torch.rand(batch_size, device=device)
        start_native = phase * max_native_start

        frames = []
        for i in range(window_length):
            t = start_native + i * ratio
            floor_t = t.floor().long()
            ceil_t = (floor_t + 1).clamp(max=lengths.long() - 1)
            w1 = (t - floor_t.float()).unsqueeze(-1)
            idx0 = starts + floor_t
            idx1 = starts + ceil_t

            def blend(buf, i0=idx0, i1=idx1, w=w1):
                return (1.0 - w) * buf[i0] + w * buf[i1]

            frame = pack_amp_frame(blend(self.base_height), blend(self.joint_position),
                                   blend(self.ee_pos_b), blend(self.base_lin_vel_b),
                                   blend(self.base_ang_vel_b), blend(self.root_rot_6d))
            frames.append(frame)
        return torch.cat(frames, dim=-1)

    def get_motion_state(
        self, num_samples: int
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Reference State Initialization (RSI): sample `num_samples` random (clip, phase) pairs
        and return the blended state at that frame -- `(root_pos_w, root_quat_w, root_lin_vel_w,
        root_ang_vel_w, joint_pos, joint_vel)` -- for `KickballState.reset` to write directly into
        the sim, matching the recipe's "80% of resets start mid-reference-motion" design."""
        device = self.device
        clip_ids = torch.multinomial(self.lengths.float(), num_samples, replacement=True)
        starts = self.starts[clip_ids]
        lengths = self.lengths[clip_ids].float()

        phase = torch.rand(num_samples, device=device)
        t = phase * (lengths - 1)
        floor_t = t.floor().long()
        ceil_t = (floor_t + 1).clamp(max=lengths.long() - 1)
        w1 = (t - floor_t.float()).unsqueeze(-1)
        idx0 = starts + floor_t
        idx1 = starts + ceil_t

        def blend(buf):
            return (1.0 - w1) * buf[idx0] + w1 * buf[idx1]

        root_pos = blend(self.base_position)
        root_lin_vel = blend(self.base_lin_vel_w)
        root_ang_vel = blend(self.base_ang_vel_w)
        joint_pos = blend(self.joint_position)
        joint_vel = blend(self.joint_velocity)

        quat0, quat1 = self.base_quat[idx0], self.base_quat[idx1]
        quat1 = torch.where((quat0 * quat1).sum(dim=-1, keepdim=True) < 0.0, -quat1, quat1)
        root_quat = torch.nn.functional.normalize((1.0 - w1) * quat0 + w1 * quat1, dim=-1)

        return root_pos, root_quat, root_lin_vel, root_ang_vel, joint_pos, joint_vel
