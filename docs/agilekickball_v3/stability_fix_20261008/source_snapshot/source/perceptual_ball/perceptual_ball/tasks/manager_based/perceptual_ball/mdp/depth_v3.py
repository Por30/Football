"""Timed synthetic depth with ground and explicitly approximate body occlusion."""
import torch
from isaaclab.utils.math import quat_apply, subtract_frame_transforms
from .perception import synthetic_ball_depth_image


class TimedDepth(synthetic_ball_depth_image):
    def __init__(self, cfg, env):
        super().__init__(cfg, env)
        self.env = env
        self.period = int(cfg.params.get("capture_period_steps", 2))
        self.max_delay = int(cfg.params.get("max_delay_steps", 2))
        self.dropout = float(cfg.params.get("frame_dropout", 0.05))
        if self.period < 1 or self.max_delay < 0 or not 0 <= self.dropout < 1:
            raise ValueError("Invalid depth timing parameters")
        shape = (env.num_envs, self.max_delay + 1, self.height, self.width)
        self.queue = torch.full(shape, self.far, device=env.device)
        self.timestamps = torch.full(shape[:2], -1., device=env.device)
        self.latest = self.queue[:, 0].clone()
        self.latest_time = self.timestamps[:, 0].clone()
        self.delivered = self.latest.clone()
        self.age_valid = torch.zeros(env.num_envs, 2, device=env.device)
        self.delay = torch.zeros(env.num_envs, dtype=torch.long, device=env.device)
        self.done_step = torch.full_like(self.delay, -1)
        self.body_radius = float(cfg.params.get("body_occlusion_radius", 0.06))
        env._soccer_depth = self

    def reset(self, env_ids=None):
        ids = slice(None) if env_ids is None else env_ids
        self.queue[ids] = self.far
        self.timestamps[ids] = -1
        self.latest[ids] = self.far
        self.latest_time[ids] = -1
        self.delivered[ids] = self.far
        self.age_valid[ids] = 0
        self.done_step[ids] = -1
        self.delay[ids] = torch.randint(self.max_delay + 1, self.delay[ids].shape, device=self.env.device)

    def _apply_depth_noise(self, depth):
        # Camera rays already have Euclidean range semantics, matching sphere intersections.
        head_pos = self.robot.data.body_link_pos_w[:, self.head_body_id]
        head_quat = self.robot.data.body_link_quat_w[:, self.head_body_id]
        from isaaclab.utils.math import quat_mul
        cam_pos = head_pos + quat_apply(head_quat, self.offset_pos)
        cam_quat = quat_mul(head_quat, self.offset_quat)
        rays = torch.stack((self.ray_x[0], self.ray_y[0], self.ray_z[0]), -1)
        directions = quat_apply(cam_quat[:, None, None].expand(-1, self.height, self.width, -1).reshape(-1, 4),
                                rays.expand(self.env.num_envs, -1, -1, -1).reshape(-1, 3))
        dz = directions[:, 2].reshape(self.env.num_envs, self.height, self.width)
        ground_t = -cam_pos[:, 2, None, None] / dz.clamp(max=-1.e-6)
        ground = torch.where((dz < -1.e-6) & (ground_t > self.near), ground_t, self.far)
        depth = torch.minimum(depth, ground)
        # Sphere proxies are a documented approximation, not a mesh-accurate camera.
        for body in range(self.robot.data.body_link_pos_w.shape[1]):
            center, _ = subtract_frame_transforms(cam_pos, cam_quat, self.robot.data.body_link_pos_w[:, body])
            along = sum(center[:, axis, None, None] * ray for axis, ray in enumerate((self.ray_x, self.ray_y, self.ray_z)))
            disc = self.body_radius ** 2 - (center.square().sum(-1)[:, None, None] - along.square())
            near = along - disc.clamp(min=0).sqrt()
            body_depth = torch.where((disc >= 0) & (near > self.near), near, self.far)
            depth = torch.minimum(depth, body_depth)
        return super()._apply_depth_noise(depth)

    def __call__(self, env, robot_cfg=None, ball_cfg=None, width=48, height=27,
                 near=0.1, far=3.0, ball_radius=0.11, offset_pos=(0., 0., 0.),
                 offset_quat=(1., 0., 0., 0.), vertical_fov_deg=58.,
                 depth_gaussian_std=0., depth_edge_dropout_prob=0.,
                 depth_edge_grad_thresh=0.15, depth_hole_dropout_prob=0.,
                 capture_period_steps=2, max_delay_steps=2, frame_dropout=0.05,
                 body_occlusion_radius=0.06):
        step = env.common_step_counter
        rows = self.done_step != step
        if not rows.any():
            return self.delivered
        capture = rows & ((step % self.period) == 0)
        if capture.any():
            image = super().__call__(env, robot_cfg, ball_cfg, width, height, near, far, ball_radius,
                                     offset_pos, offset_quat, vertical_fov_deg,
                                     depth_gaussian_std, depth_edge_dropout_prob,
                                     depth_edge_grad_thresh, depth_hole_dropout_prob)
            capture &= torch.rand(env.num_envs, device=env.device) >= self.dropout
            self.latest[capture] = image[capture]
            self.latest_time[capture] = step * env.step_dt
        self.queue[rows, 1:] = self.queue[rows, :-1].clone()
        self.timestamps[rows, 1:] = self.timestamps[rows, :-1].clone()
        self.queue[rows, 0] = self.latest[rows]
        self.timestamps[rows, 0] = self.latest_time[rows]
        indices = rows.nonzero().flatten()
        self.delivered[rows] = self.queue[indices, self.delay[rows]]
        stamp = self.timestamps[indices, self.delay[rows]]
        valid = stamp >= 0
        self.age_valid[rows, 0] = torch.where(valid, step * env.step_dt - stamp, 0.)
        self.age_valid[rows, 1] = valid.float()
        self.done_step[rows] = step
        return self.delivered


def depth_timing(env):
    depth = getattr(env, "_soccer_depth", None)
    return depth.age_valid.clone() if depth is not None else torch.zeros(env.num_envs, 2, device=env.device)
