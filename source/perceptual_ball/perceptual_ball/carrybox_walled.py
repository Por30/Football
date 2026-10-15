"""Tensor-only contracts for G1 FindBox wall variants (no policy privileged input)."""
import math
import torch


class YawCurriculum:
    def __init__(self, variant):
        if variant not in ('walled3', 'walled4'):
            raise ValueError(variant)
        self.variant, self.anchor, self.iteration = variant, None, None

    def set_iteration(self, iteration):
        if iteration < 0:
            raise ValueError('Training iteration must be nonnegative')
        if self.anchor is None:
            self.anchor = int(iteration)
        self.iteration = int(iteration)

    @property
    def degrees(self):
        effective = 0 if self.anchor is None else max(0, self.iteration - self.anchor)
        # Both obstacle variants use the same process-anchored difficulty.
        knots = ((0, 0.), (10000, 10.), (20000, 30.), (30000, 180.))
        for (a, x), (b, y) in zip(knots, knots[1:]):
            if effective <= b:
                return x + (y-x) * max(0., (effective-a)/(b-a))
        return 180.


def search_reward(marked, signed_error, distance, yaw_rate):
    error = signed_error.abs()
    gate = marked & (error > math.pi / 4) & (distance > .7)
    value = .7 * torch.exp(-.75 * error) + .3 * torch.tanh((signed_error.sign()*yaw_rate).clamp_min(0))
    return torch.where(gate, value, 0.)


def corrupt_depth_m(depth, gaussian_std=.06, edge_threshold=.15, edge_probability=.05,
                    hole_probability=.02, stereo_near=.024, stereo_far=.09):
    """Handoff v2/v2.5 noise in metres; preserve misses and the optical near plane.

    Adjacent depth discontinuities mark both pixels, without wraparound at borders.
    The G1 adaptations (miss preservation and final 0.1m clamp) are explicit.
    """
    clean = depth.nan_to_num(nan=3., posinf=3., neginf=3.).clamp(.1, 3.)
    valid = torch.isfinite(depth) & (depth < 3.) & (depth >= .1)
    noisy = clean + torch.randn_like(clean) * gaussian_std
    edge = torch.zeros_like(clean, dtype=torch.bool)
    dx = (noisy[..., 1:] - noisy[..., :-1]).abs() > edge_threshold
    dy = (noisy[..., 1:, :] - noisy[..., :-1, :]).abs() > edge_threshold
    edge[..., 1:] |= dx
    edge[..., :-1] |= dx
    edge[..., 1:, :] |= dy
    edge[..., :-1, :] |= dy
    missing = (~valid) | (edge & (torch.rand_like(clean) < edge_probability))
    missing |= torch.rand_like(clean) < hole_probability
    noisy = torch.where(missing, 3., noisy)
    sigma = stereo_near + (stereo_far-stereo_near) * noisy.clamp(0., 3.) / 3.
    noisy = (noisy + torch.randn_like(noisy) * sigma).clamp(.1, 3.)
    return torch.where(missing, 3., noisy)


class PairedDepthBuffer:
    """Delay/freeze captured depth and its label together; exactly one capture per step/env."""
    def __init__(self, depth, pose, max_delay=2):
        n = len(depth)
        self.depth = depth[:, None].repeat(1, max_delay+1, 1, 1).clone()
        self.pose = pose[:, None].repeat(1, max_delay+1, 1).clone()
        self.output_depth, self.output_pose = depth.clone(), pose.clone()
        self.last_step = torch.full((n,), -1, device=depth.device, dtype=torch.long)
        self.fresh = torch.ones(n, device=depth.device, dtype=torch.bool)
        self.freeze_left = torch.zeros(n, device=depth.device, dtype=torch.long)
        self.max_delay = max_delay

    def reset(self, ids):
        self.fresh[ids] = True
        self.last_step[ids] = -1
        self.freeze_left[ids] = 0

    def update(self, step, depth, pose, delays, freeze_steps):
        update = self.last_step != step
        fresh = self.fresh & update
        ids = update.nonzero().flatten()
        if not len(ids):
            return self.output_depth, self.output_pose
        self.depth[ids] = torch.cat((depth[ids, None], self.depth[ids, :-1]), 1)
        self.pose[ids] = torch.cat((pose[ids, None], self.pose[ids, :-1]), 1)
        self.depth[fresh] = depth[fresh, None]
        self.pose[fresh] = pose[fresh, None]
        frozen = (self.freeze_left > 0) & ~fresh
        deliver = update & ~frozen
        rows = deliver.nonzero().flatten()
        delay = delays[rows].clamp(0, self.max_delay)
        self.output_depth[rows] = self.depth[rows, delay]
        self.output_pose[rows] = self.pose[rows, delay]
        self.freeze_left[ids] = (self.freeze_left[ids]-1).clamp_min(0)
        self.freeze_left[rows] = freeze_steps[rows]
        self.freeze_left[fresh] = 0
        self.last_step[ids] = step
        self.fresh[ids] = False
        return self.output_depth, self.output_pose
