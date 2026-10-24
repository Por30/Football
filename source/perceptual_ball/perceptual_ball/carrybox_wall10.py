"""Wall10 tensor contracts: PhysHSI training with FindBox lift-and-hold semantics."""
import torch
from isaaclab.utils.math import quat_apply_inverse, euler_xyz_from_quat
from .carrybox_amp import FindBoxMotionLibrary
from .carrybox_wall5 import pack_task_frame

FEATURE_SCHEMA = 'physhsi_height1_joints29_ends15_box3_lin3_ang3_rot6_v1'
SOURCE_WEIGHTS = {'loco_direction': 1., 'pickUp': 4., 'carryWith': 5.}


def pack_frame(joints, quat, ends, linear, angular, box):
    frame = pack_task_frame(joints, quat, ends, linear, angular, box)
    return torch.cat((frame[..., :45], frame[..., 57:60], frame[..., 45:57]), -1)


class Wall10MotionLibrary(FindBoxMotionLibrary):
    """Native feature interpolation and 0.95--1.05 time jitter as in PhysHSI.

    The FindBox manifest still validates every byte. Retained source clip weights
    are 1/4/5; the project hold clip replaces carrying/putting-down demonstrations.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        frames = []
        for name, (joints, _, quat, _) in zip(self.clip_names, self.clips):
            data = torch.load(self.root / name, map_location=self.device, weights_only=True)
            position = data['base_position'].float()
            linear = torch.cat(((position[1:] - position[:-1]) * self.fps,
                                (position[-1:] - position[-2:-1]) * self.fps))
            # Match the source's unwrapped Euler finite-difference approximation.
            rpy = torch.stack(euler_xyz_from_quat(quat), -1)
            delta = torch.remainder(rpy[1:] - rpy[:-1] + torch.pi, 2 * torch.pi) - torch.pi
            angular_world = torch.cat((delta, delta[-1:])) * self.fps
            angular = quat_apply_inverse(quat, angular_world)
            frame = pack_frame(joints, quat, data['link_position'][:, :5].float(),
                               linear, angular, data['box_pos_local'].float())
            frame[:, :1] = data['base_height'].float().unsqueeze(-1)
            frames.append(frame)
        self.frames = torch.cat(frames)
        self.offsets = torch.cat((self.lengths.new_zeros(1), self.lengths.cumsum(0)[:-1]))
        self.weights = self.weights.new_tensor([SOURCE_WEIGHTS[g] for g in self.clip_groups])
        self.weights /= self.weights.sum()
        self.metadata.update(feature_schema=FEATURE_SCHEMA, frame_dim=60,
                             clip_weights=self.weights.tolist(), time_jitter=[.95, 1.05],
                             interpolation='native_features', normalization='none',
                             angular_velocity='source_unwrapped_euler_difference_rotated_to_body')

    def windows(self, clip_ids, native_starts, ratio=None):
        ratio = self.fps / self.env_fps if ratio is None else ratio
        if isinstance(ratio, torch.Tensor) and ratio.ndim == 1:
            ratio = ratio[:, None]
        times = native_starts[:, None] + torch.arange(self.window_length, device=self.device) * ratio
        last = self.lengths[clip_ids, None] - 1
        if not torch.isfinite(times).all() or (times < 0).any() or (times > last + 1.e-5).any():
            raise ValueError('Wall10 AMP window crosses a clip boundary')
        times = torch.minimum(times, last)
        lo = times.floor().long()
        hi = torch.minimum(lo + 1, last)
        weight = (times - lo).unsqueeze(-1)
        offsets = self.offsets[clip_ids, None]
        return (self.frames[offsets + lo] * (1 - weight) + self.frames[offsets + hi] * weight).flatten(1)

    def sample_window_parameters(self, batch_size):
        """Keep source RNG order; interpolation can then batch logical draws."""
        ids = torch.multinomial(self.weights, batch_size, replacement=True)
        lengths = self.lengths[ids].float()
        # Source samples a full-clip time and clamps the tail, rather than
        # rescaling uniform samples over the shortened valid interval.
        limit = 1 - (self.window_length * self.fps / self.env_fps + 2) / lengths
        starts = torch.minimum(torch.rand(batch_size, device=self.device), limit) * (lengths - 1)
        ratio = self.fps / self.env_fps * torch.empty((), device=self.device).uniform_(.95, 1.05)
        return ids, starts, ratio

    def sample_expert_amp_obs(self, batch_size, return_clip_ids=False):
        ids, starts, ratio = self.sample_window_parameters(batch_size)
        windows = self.windows(ids, starts, ratio)
        return (windows, ids) if return_clip_ids else windows


def lift_hold_mask(clearance, contacts, box_upright, robot_upright, head_height,
                   root_speed, root_yaw_speed, box_speed, drift, box_height):
    """Success requires physical bilateral contact and stationary upright carrying."""
    return ((clearance > .10) & contacts.all(-1) & (box_upright > .8)
            & (robot_upright > .95) & (head_height > 1.05) & (box_height >= .70)
            & (root_speed < .15) & (root_yaw_speed < .3)
            & (box_speed < .15) & (drift < .35))


def task_rewards(distance, towards, bearing, hand_error, box_height,
                 held, head_height, linear_speed, angular_speed, box_speed, drift):
    """Source walk/carry-up; hold replaces relocation/put-down/hand-free stand-up."""
    walk = torch.exp(-5 * (.85 - towards).square()) + .5 * torch.exp(-.75 * bearing.abs())
    walk = torch.where(distance < .7, 1.5, walk)
    carry = (.7 * torch.exp(-3 * hand_error)
             + 2. * torch.exp(-3 * (.72 - box_height).clamp_min(0))) * (distance <= .7)
    # Holding must not reward returning arms to the empty-hand default pose.
    hold = (.5 * torch.exp(-2 * (1.15 - head_height).clamp_min(0))
            + torch.exp(-3 * linear_speed - angular_speed - 3 * box_speed)
            + .5 * torch.exp(-10 * drift.square())) * held
    return dict(walk_task=walk, carryup_task=carry, standup_task=hold)
