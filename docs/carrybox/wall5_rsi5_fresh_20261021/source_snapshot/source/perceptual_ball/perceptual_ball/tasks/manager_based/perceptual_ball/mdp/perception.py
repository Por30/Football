# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import math
import torch
from typing import TYPE_CHECKING

from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import ManagerTermBase, SceneEntityCfg
from isaaclab.utils.math import quat_apply, quat_mul, subtract_frame_transforms

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv
    from isaaclab.managers import ObservationTermCfg


class synthetic_ball_depth_image(ManagerTermBase):
    """Per-pixel ray-cast depth image against the ball, without `isaaclab.sensors.RayCaster`.

    A real rendered camera (`TiledCamera`) is by far the dominant cost of this task and forces
    `num_envs` far below what a proprioception-only task can run. `isaaclab.sensors.RayCaster`/
    `RayCasterCamera` would be the natural fast alternative, but that sensor is built around a
    single, shared, world-frame-static warp mesh (its own docstring: "currently only static
    meshes are supported") -- it has no notion of a mesh whose pose updates every physics step
    per environment, which is exactly what the ball is. Forcing it to track the ball would mean
    rebuilding its warp mesh (or a whole custom ray/mesh pipeline) every step.

    Since the ball is a perfect sphere, casting a ray per pixel against it has a closed-form
    solution, so none of that machinery is needed: for a camera ray direction `d` (unit vector)
    and the ball's center `c` in the camera frame with radius `r`, the near intersection distance
    is `t = c.d - sqrt(r^2 - (|c|^2 - (c.d)^2))` when the discriminant is non-negative. This is a
    real per-pixel ray-object intersection (a curved silhouette, not a flat painted disk) computed
    directly from the ball's current pose, so it stays correct as the ball moves -- just without
    ever building a mesh or calling into `isaaclab.sensors`. It still ignores occlusion by the
    robot's own body or other objects (there is only one object to intersect against); swap in a
    real `Camera`/`TiledCamera`/`RayCasterCamera` sensor once training speed is no longer the
    bottleneck or a richer scene needs to show up in the image.
    """

    def __init__(self, cfg: ObservationTermCfg, env: ManagerBasedRLEnv):
        super().__init__(cfg, env)

        robot_cfg: SceneEntityCfg = cfg.params["robot_cfg"]
        self.robot: Articulation = env.scene[robot_cfg.name]
        self.ball: RigidObject = env.scene[cfg.params["ball_cfg"].name]
        self.head_body_id: int = robot_cfg.body_ids[0]

        self.width: int = cfg.params["width"]
        self.height: int = cfg.params["height"]
        self.near: float = cfg.params["near"]
        self.far: float = cfg.params["far"]
        self.ball_radius: float = cfg.params["ball_radius"]
        # sensor-noise model, off by default so the v3 task (Template-Perceptual-Ball-v0) keeps
        # its exact noiseless image; soccer-v2 turns it on (see soccer_v2_env_cfg.py)
        self.depth_gaussian_std: float = cfg.params.get("depth_gaussian_std", 0.0)
        self.depth_edge_dropout_prob: float = cfg.params.get("depth_edge_dropout_prob", 0.0)
        self.depth_edge_grad_thresh: float = cfg.params.get("depth_edge_grad_thresh", 0.15)
        self.depth_hole_dropout_prob: float = cfg.params.get("depth_hole_dropout_prob", 0.0)
        # pixel focal length derived from the vertical FOV (matches the x2_kickball_depth_v3
        # recipe's "垂直FOV 58°" spec directly, rather than a focal-length/aperture pair)
        vfov_rad = math.radians(cfg.params["vertical_fov_deg"])
        focal_px: float = self.height / (2.0 * math.tan(vfov_rad / 2.0))

        offset_pos = torch.tensor(cfg.params["offset_pos"], device=env.device, dtype=torch.float32)
        offset_quat = torch.tensor(cfg.params["offset_quat"], device=env.device, dtype=torch.float32)
        self.offset_pos = offset_pos.unsqueeze(0).repeat(env.num_envs, 1)
        self.offset_quat = offset_quat.unsqueeze(0).repeat(env.num_envs, 1)

        # per-pixel camera ray directions, in the camera's own frame (x=right, y=down, z=forward,
        # matching the "ros" offset convention), normalized to unit length. Shape (1, H, W).
        grid_v, grid_u = torch.meshgrid(
            torch.arange(self.height, device=env.device, dtype=torch.float32),
            torch.arange(self.width, device=env.device, dtype=torch.float32),
            indexing="ij",
        )
        dir_x = (grid_u - self.width / 2.0) / focal_px
        dir_y = (grid_v - self.height / 2.0) / focal_px
        dir_norm = torch.sqrt(dir_x**2 + dir_y**2 + 1.0)
        self.ray_x = (dir_x / dir_norm).unsqueeze(0)
        self.ray_y = (dir_y / dir_norm).unsqueeze(0)
        self.ray_z = (1.0 / dir_norm).unsqueeze(0)

    def __call__(
        self,
        env: ManagerBasedRLEnv,
        robot_cfg: SceneEntityCfg,
        ball_cfg: SceneEntityCfg,
        width: int,
        height: int,
        near: float,
        far: float,
        ball_radius: float,
        offset_pos: tuple[float, float, float],
        offset_quat: tuple[float, float, float, float],
        vertical_fov_deg: float,
        depth_gaussian_std: float = 0.0,
        depth_edge_dropout_prob: float = 0.0,
        depth_edge_grad_thresh: float = 0.15,
        depth_hole_dropout_prob: float = 0.0,
    ) -> torch.Tensor:
        head_pos_w = self.robot.data.body_link_pos_w[:, self.head_body_id, :]
        head_quat_w = self.robot.data.body_link_quat_w[:, self.head_body_id, :]
        cam_pos_w = head_pos_w + quat_apply(head_quat_w, self.offset_pos)
        cam_quat_w = quat_mul(head_quat_w, self.offset_quat)

        # ball center in the camera frame
        ball_pos_c, _ = subtract_frame_transforms(cam_pos_w, cam_quat_w, self.ball.data.root_pos_w[:, :3])
        cx = ball_pos_c[:, 0].view(-1, 1, 1)
        cy = ball_pos_c[:, 1].view(-1, 1, 1)
        cz = ball_pos_c[:, 2].view(-1, 1, 1)

        # ray-sphere intersection, per pixel: t = c.d - sqrt(r^2 - (|c|^2 - (c.d)^2))
        t_center = cx * self.ray_x + cy * self.ray_y + cz * self.ray_z
        center_dist_sq = cx * cx + cy * cy + cz * cz
        perp_dist_sq = center_dist_sq - t_center**2
        discriminant = self.ball_radius**2 - perp_dist_sq

        hits = discriminant >= 0.0
        t_hit = t_center - torch.sqrt(discriminant.clamp(min=0.0))
        visible = hits & (t_hit > self.near) & (t_hit < self.far)

        depth = torch.where(visible, t_hit, torch.full_like(t_hit, self.far))
        return self._apply_depth_noise(depth)

    def _apply_depth_noise(self, depth: torch.Tensor) -> torch.Tensor:
        """The v5/v11 depth-noise model, in its order: Gaussian, edge dropout, hole dropout, clamp.

        Every term is a no-op at its 0.0 default, so the v3 task keeps its exact analytic image.

        The Gaussian standard deviation is `depth_gaussian_std * far` -- an absolute distance
        (0.02 * 3.0 = 0.06 m at the spec's settings), not a fraction of each pixel's own range.
        "Edge dropout" then drops pixels that sit on a depth discontinuity, which on this image
        means the ball's silhouette: a real stereo camera is least reliable exactly there, and
        without it the policy could read the ball's outline more sharply than hardware allows.
        A dropped pixel reads `far`, the same "no return" value the background carries.
        """
        if self.depth_gaussian_std > 0.0:
            depth = depth + torch.randn_like(depth) * (self.depth_gaussian_std * self.far)

        if self.depth_edge_dropout_prob > 0.0:
            grad_x = torch.zeros_like(depth)
            grad_y = torch.zeros_like(depth)
            grad_x[:, :, 1:] = (depth[:, :, 1:] - depth[:, :, :-1]).abs()
            grad_y[:, 1:, :] = (depth[:, 1:, :] - depth[:, :-1, :]).abs()
            on_edge = (grad_x + grad_y) > self.depth_edge_grad_thresh
            dropped = on_edge & (torch.rand_like(depth) < self.depth_edge_dropout_prob)
            depth = torch.where(dropped, torch.full_like(depth, self.far), depth)

        if self.depth_hole_dropout_prob > 0.0:
            dropped = torch.rand_like(depth) < self.depth_hole_dropout_prob
            depth = torch.where(dropped, torch.full_like(depth, self.far), depth)

        return depth.clamp(0.0, self.far)
