"""Read-only play overlay for the current, untimed synthetic depth observation."""
import torch
from isaaclab.utils.math import quat_apply, quat_mul
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.perception import synthetic_ball_depth_image


def depth_ray_geometry(term, depth):
    """World origin and pixel endpoints; depth is Euclidean range, not optical z."""
    n = term.offset_pos.shape[0]
    if tuple(depth.shape) != (n, term.height, term.width):
        raise ValueError(f'--visray expected depth [{n}, {term.height}, {term.width}], got {tuple(depth.shape)}')
    data = term.robot.data
    body_pos = data.body_link_pos_w[:, term.head_body_id]
    body_quat = data.body_link_quat_w[:, term.head_body_id]
    origin = body_pos + quat_apply(body_quat, term.offset_pos)
    orientation = quat_mul(body_quat, term.offset_quat)
    rays = torch.stack((term.ray_x[0], term.ray_y[0], term.ray_z[0]), -1).reshape(-1, 3)
    count = rays.shape[0]
    directions = quat_apply(orientation[:, None].expand(n, count, 4).reshape(-1, 4),
                            rays[None].expand(n, count, 3).reshape(-1, 3)).reshape(n, count, 3)
    ranges = depth.reshape(n, count)
    endpoints = origin[:, None] + directions * ranges.clamp(0., term.far)[..., None]
    valid = torch.isfinite(ranges) & torch.isfinite(endpoints).all(-1)
    hits = valid & (ranges > term.near) & (ranges < term.far - 1.e-5)
    return origin, endpoints, valid, hits


class DepthRayVisualizer:
    """Sparse green rays and all pixel endpoints, using existing observation history."""
    def __init__(self, env, draw=None):
        manager = env.observation_manager
        names = manager.active_terms.get('perception', [])
        if 'depth_image' not in names:
            raise ValueError('--visray requires the synthetic perception/depth_image observation')
        # This Isaac Lab version exposes names publicly, but only has private term configs.
        self.term = manager._group_obs_term_cfgs['perception'][names.index('depth_image')].func
        if type(self.term) is not synthetic_ball_depth_image:
            raise ValueError('--visray currently supports untimed synthetic depth (AgileKickball-v0/v1); '
                             'delayed depth requires its capture-time pose')
        t = self.term
        rows = sorted(set(range(0, t.height, 4)) | {t.height-1})
        cols = sorted(set(range(0, t.width, 6)) | {t.width-1})
        self.line_ids = torch.tensor([r*t.width+c for r in rows for c in cols], device=t.offset_pos.device)
        if draw is None:
            from isaacsim.core.utils.extensions import enable_extension
            enable_extension('isaacsim.util.debug_draw')
            from isaacsim.util.debug_draw import _debug_draw
            draw = _debug_draw.acquire_debug_draw_interface()
        self.draw = draw

    def update(self, observations):
        # CircularBuffer history is oldest -> newest. Do not recompute observations:
        # doing so would consume noise RNG and can change the policy's input/history.
        history = observations['perception']
        if history.ndim != 4 or history.shape[1] < 1:
            raise ValueError('--visray requires unflattened [N, history, H, W] depth observations')
        with torch.no_grad():
            origin, endpoints, valid, hits = depth_ray_geometry(self.term, history[:, -1])
            selected = endpoints[:, self.line_ids]
            line_valid = valid[:, self.line_ids]
            starts = origin[:, None].expand_as(selected)[line_valid].cpu().tolist()
            ends = selected[line_valid].cpu().tolist()
            # Dim far-range pixels outline the sampled FOV; bright larger pixels mark returns.
            points = endpoints[valid].cpu().tolist()
            returned = hits[valid].cpu().tolist()
        self.draw.clear_lines()
        self.draw.clear_points()
        if starts:
            self.draw.draw_lines(starts, ends, [(0., 1., 0., .35)]*len(starts), [1.]*len(starts))
        if points:
            colors = [(0., 1., 0., 1. if hit else .3) for hit in returned]
            sizes = [5. if hit else 2. for hit in returned]
            self.draw.draw_points(points, colors, sizes)

    def close(self):
        self.draw.clear_lines()
        self.draw.clear_points()
