"""Wall11 tensor-only depth corruption and collision-clear obstacle layout."""
import math
import torch
from .carrybox_walled import corrupt_depth_m


DEPTH_NOISE = dict(gaussian_std=.02, edge_threshold=.15, edge_probability=.05,
                   hole_probability=.02, stereo_near=.008, stereo_far=.03)


class NoisyDepthFrame:
    """One noisy capture per environment/control step, including terminal reads."""
    def __init__(self, depth):
        self.output = torch.empty_like(depth)
        self.last_step = torch.full((len(depth),), -1, device=depth.device, dtype=torch.long)

    def reset(self, ids):
        self.last_step[ids] = -1

    def update(self, step, depth, noise):
        ids = (self.last_step != step).nonzero().flatten()
        if len(ids):
            self.output[ids] = corrupt_depth_m(depth[ids], **noise)
            self.last_step[ids] = step
        return self.output


def obstacle_layout(robot_xy, body_xy, box_xy, box_size):
    """Enclose the reset workspace; columns never spawn through the approach path.

    All positions are world XY. A conservative disk contains every robot link
    origin (+50 cm) and the oriented box/support (+10 cm). The columns sit
    outside it with another 35 cm to their centres. No rejection loop or CPU RNG.
    Returns column centres, wall centre/yaw and the protected disk radius.
    """
    n = len(robot_xy)
    centre = (robot_xy + box_xy) * .5
    robot_bound = (body_xy - centre[:, None]).norm(dim=-1).amax(-1) + .5
    box_bound = (box_xy - centre).norm(dim=-1) + torch.maximum(
        box_size[:, :2].norm(dim=-1) * .5, box_size.new_full((n,), math.sqrt(.08))) + .1
    protected = torch.maximum(robot_bound, box_bound)
    radius = (protected + .35).clamp_min(1.35) + torch.rand_like(protected) * .35
    bearing = torch.atan2(box_xy[:, 1] - robot_xy[:, 1], box_xy[:, 0] - robot_xy[:, 0])
    angle = bearing + (torch.rand_like(bearing) * 2 - 1) * math.pi / 3
    angles = angle[:, None] + torch.arange(3, device=robot_xy.device) * (2 * math.pi / 3)
    angles = angles + (torch.rand(n, 3, device=robot_xy.device) * 2 - 1) * math.pi / 12
    columns = centre[:, None] + radius[:, None, None] * torch.stack((angles.cos(), angles.sin()), -1)
    wall_yaw = torch.rand_like(bearing) * (2 * math.pi)
    wall_radius = radius + .45 + torch.rand_like(radius) * .35
    wall_xy = centre + wall_radius[:, None] * torch.stack((wall_yaw.cos(), wall_yaw.sin()), -1)
    return columns, wall_xy, wall_yaw, protected
