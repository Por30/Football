"""Wall5 task-conditioned AMP and ground-pickup reference selection."""
from pathlib import Path
import torch
from .carrybox_amp import AMP_WINDOW, FindBoxMotionLibrary, DEFAULT_DATASET_PATH

WALL5_FRAME_DIM = 60
WALL5_FEATURE_SCHEMA = 'height1_joints29_ends15_lin3_ang3_rot6_box3_pelvis_v2'
GROUND_DATASET_PATH = str(Path(__file__).resolve().parent / 'assets/motions/findbox/ground_pickup')
AMP_DATASET_PATH = DEFAULT_DATASET_PATH  # all three complete pickups; RSI remains ground-only
GROUND_RESET_PROFILE = 'ground_box_5mm_pickup_prefix_rise5mm_v1'


def grasp_reward_geometry():
    """Metres; calibrated with all 499 pickup frames in real G1 FK (2026-10-22).

    Opposing palms approach within 4–8 cm of the box surface; ground pickup
    starts grasping around 0.49 m pelvis XY distance. Use a broad reach signal
    and a 0.45–0.60 m stance band, not the old saturated near-box walk bonus.
    """
    return dict(profile='bilateral_surface_contact_clearance_v23',
                stance_target_m=.52, stance_width_m=.12,
                travel_end_m=.60, travel_blend_m=.20,
                crowding_start_m=.40, crowding_width_m=.15,
                reach_gate_3d_m=.90, reach_gate_fade_m=.08,
                palm_surface_tolerance_m=.04, reach_scale_m=.18,
                contact_threshold_n=1., contact_saturation_n=5.,
                lift_start_m=.01, lift_span_m=.24,
                stance_weight=.2, crowding_weight=.5,
                reach_weight=1.5, contact_weight=.5,
                bilateral_weight=1.5, lift_weight=2.5)


def grasp_components(delta, towards, bearing, palms_box_frame, half_size,
                     hand_force, bottom_clearance, g):
    """Reward-only tensor equations; all geometry in metres, box-local palms.

    Both palms must approach the actual oriented box separately. Contact and
    lift require Box-filtered forces, with saturated force contribution. A
    lifted box without two-hand contact earns no lift reward.
    """
    xy, xyz = delta[:, :2].norm(dim=-1), delta.norm(dim=-1)
    surface = (palms_box_frame.abs() - half_size).clamp_min(0.).norm(dim=-1)
    error = (surface - g['palm_surface_tolerance_m']).clamp_min(0.)
    opposite = (-palms_box_frame[:, 0, :2] * palms_box_frame[:, 1, :2]
                / half_size[:2].square()).amax(-1).clamp(0., 1.)
    reach = torch.exp(-error.mean(-1) / g['reach_scale_m']) * (.5 + .5 * opposite)
    gate = ((g['reach_gate_3d_m'] + g['reach_gate_fade_m'] - xyz)
            / g['reach_gate_fade_m']).clamp(0., 1.)
    contact = (hand_force / g['contact_saturation_n']).clamp(0., 1.)
    contact *= hand_force > g['contact_threshold_n']
    bilateral = contact.amin(-1) * opposite
    lift = ((bottom_clearance - g['lift_start_m']) / g['lift_span_m']).clamp(0., 1.)
    # Only reaching/stance use a distance gate. A physically held box must not
    # lose its contact/lift rewards simply because the torso leans away.
    carryup = (g['reach_weight'] * reach * gate + g['contact_weight'] * contact.mean(-1)
               + g['bilateral_weight'] * bilateral + g['lift_weight'] * bilateral * lift)
    travel = ((xy - g['travel_end_m']) / g['travel_blend_m']).clamp(0., 1.)
    speed = torch.exp(-5. * (.85 - towards).square())
    heading = torch.exp(-.75 * bearing)
    stance = torch.exp(-((xy - g['stance_target_m']) / g['stance_width_m']).square()) * heading
    crowded = ((g['crowding_start_m'] - xy) / g['crowding_width_m']).clamp(0., 1.).square()
    # Heading alone must not pay more for standing far away than for reaching.
    heading_progress = (towards / .85).clamp(0., 1.)
    walk = travel * (speed + .5 * heading * heading_progress) + (1. - lift) * (
        g['stance_weight'] * stance - g['crowding_weight'] * crowded)
    return dict(walk_task=walk, carryup_task=carryup, reach=reach * gate,
                bilateral=bilateral, lift=bilateral * lift,
                both_contacts=(hand_force > g['contact_threshold_n']).all(-1),
                surface_distance=surface, opposite=opposite, crowding=crowded * (1. - lift))


def ground_pickup_frame_ids(data):
    """Continuous pre-lift prefix of a native ground pickup, before foot correction.

    The source stores box displacement in a yaw-aligned world frame, so its z
    adds to base_height (+ the existing 5 cm reference-root compensation).
    A 2 cm tolerance identifies the ground-origin clip; a 5 mm rise relative to
    its initial median ends the reset prefix. AMP may retain the full lift.
    """
    height, position = data['base_height'], data['box_pos_local']
    n = len(data['joint_position'])
    if (height.shape != (n,) or position.shape != (n, 3) or n < 2
            or not torch.isfinite(height).all() or not torch.isfinite(position).all()):
        raise ValueError('Invalid ground-pickup reference geometry')
    bottom = height + .05 + position[:, 2] - .125
    initial = bottom[:min(20, n)].median()
    if initial.abs() > .02:
        return torch.empty(0, device=height.device, dtype=torch.long)
    invalid = ((bottom > initial + .005) | (bottom < -.02)).nonzero().flatten()
    end = min(int(invalid[0]) if len(invalid) else n, n - 1)
    # Keep a following source frame for the reference velocity calculation.
    return torch.arange(end, device=height.device)


# Each is a rigid link origin, not its COM or the rubber-hand collision centre.
AMP_BODY_NAMES = ('left_palm_link', 'right_palm_link', 'left_ankle_pitch_link',
                  'right_ankle_pitch_link', 'mid360_link')


def pack_task_frame(joints, root_quat, ends_world, linear_world, angular_body, box_world):
    """60D: height, joints, ends, lin, ang, yaw-free x/z axes, bounded box.

    ends_world and box_world are displacements from the pelvis link origin,
    expressed in world axes. Velocities refer to that same link origin.
    """
    from isaaclab.utils.math import quat_apply_inverse, quat_mul, quat_conjugate, yaw_quat, matrix_from_quat
    shape = joints.shape[:-1]
    q = root_quat.reshape(-1, 4)
    ends = ends_world.reshape(-1, 5, 3)
    height = -ends[:, 2:4, 2].amin(-1, keepdim=True)
    local_ends = quat_apply_inverse(q[:, None].expand(-1, 5, -1).reshape(-1, 4), ends.reshape(-1, 3)).reshape(-1, 15)
    lin = quat_apply_inverse(q, linear_world.reshape(-1, 3))
    box = quat_apply_inverse(q, box_world.reshape(-1, 3))
    distance = box[:, :2].norm(dim=-1, keepdim=True)
    far = distance > .7
    box = torch.cat((box[:, :2] * (.7 / distance.clamp_min(.7)), torch.where(far, 0., box[:, 2:3])), -1)
    rotation = matrix_from_quat(quat_mul(quat_conjugate(yaw_quat(q)), q))
    rot6 = torch.cat((rotation[..., 0], rotation[..., 2]), -1)
    return torch.cat((height, joints.reshape(-1, 29), local_ends, lin,
                      angular_body.reshape(-1, 3), rot6, box), -1).reshape(*shape, 60)


class Wall5MotionLibrary(FindBoxMotionLibrary):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata.update(feature_schema=WALL5_FEATURE_SCHEMA, frame_dim=WALL5_FRAME_DIM,
                             end_links=list(AMP_BODY_NAMES), box_xy_cap_m=.7,
                             angular_velocity='shortest_quaternion_difference_body')
        self.task_clips = []
        for name, (joints, _, quat, angular) in zip(self.clip_names, self.clips):
            data = torch.load(self.root / name, map_location=self.device, weights_only=True)
            n = len(joints)
            for key, size in (('link_position', (n, 6, 3)), ('base_position', (n, 3)), ('box_pos_local', (n, 3))):
                if data[key].shape != size or not torch.isfinite(data[key]).all():
                    raise ValueError(f'Invalid task AMP {key}: {name}')
            linear = torch.empty_like(data['base_position'])
            linear[:-1] = (data['base_position'][1:] - data['base_position'][:-1]) * self.fps
            linear[-1] = linear[-2]
            self.task_clips.append((data['link_position'][:, :5].float(), linear.float(), data['box_pos_local'].float()))

        # Cache native states, never task features: interpolation precedes rotations
        # and the nonlinear box-distance cap. Clip offsets keep windows independent.
        self._raw_frames = torch.cat([
            torch.cat((joints, quat, angular, ends.flatten(1), linear, box), -1)
            for (joints, _, quat, angular), (ends, linear, box) in zip(self.clips, self.task_clips)
        ])
        self._clip_offsets = torch.cat((self.lengths.new_zeros(1), self.lengths.cumsum(0)[:-1]))
        self._window_times = torch.arange(self.window_length, device=self.device) * self.fps / self.env_fps

    def windows(self, clip_ids, native_starts):
        if ((~torch.isfinite(native_starts)).any() | (clip_ids < 0).any() | (clip_ids >= self.num_clips).any()):
            raise ValueError('Invalid task AMP window request')
        times = native_starts[:, None] + self._window_times
        last = self.lengths[clip_ids, None] - 1
        if ((times < 0).any() | (times > last + 1.e-5).any()):
            raise ValueError('Task AMP window would cross a clip boundary')
        times = torch.minimum(times, last)
        lo = times.floor().long()
        hi = torch.minimum(lo + 1, last)
        weight = (times - lo).unsqueeze(-1)
        offsets = self._clip_offsets[clip_ids, None]
        a, b = self._raw_frames[lo + offsets], self._raw_frames[hi + offsets]
        raw = a * (1 - weight) + b * weight
        q0, q1 = a[..., 29:33], b[..., 29:33]
        q1 = torch.where((q0*q1).sum(-1, keepdim=True) < 0, -q1, q1)
        q = torch.nn.functional.normalize(q0*(1-weight)+q1*weight, dim=-1)
        result = pack_task_frame(raw[..., :29], q, raw[..., 36:51].reshape(*times.shape, 5, 3),
                                 raw[..., 51:54], raw[..., 33:36], raw[..., 54:57])
        return result.flatten(1)
