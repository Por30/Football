"""Wall5 task-conditioned AMP and ground-pickup reference selection."""
from pathlib import Path
import torch
from .carrybox_amp import AMP_WINDOW, FindBoxMotionLibrary

WALL5_FRAME_DIM = 60
WALL5_FEATURE_SCHEMA = 'height1_joints29_ends15_lin3_ang3_rot6_box3_pelvis_v2'
GROUND_DATASET_PATH = str(Path(__file__).resolve().parent / 'assets/motions/findbox/ground_pickup')
GROUND_RESET_PROFILE = 'ground_box_5mm_pickup_prefix_rise5mm_v1'


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

    def windows(self, clip_ids, native_starts):
        result = torch.empty((len(clip_ids), self.window_length, WALL5_FRAME_DIM), device=self.device)
        if (not torch.isfinite(native_starts).all() or (clip_ids < 0).any() or (clip_ids >= self.num_clips).any()):
            raise ValueError('Invalid task AMP window request')
        for clip_id in clip_ids.unique().tolist():
            mask = clip_ids == clip_id
            joints, _, quat, angular = self.clips[clip_id]
            ends, linear, box = self.task_clips[clip_id]
            times = native_starts[mask, None] + torch.arange(self.window_length, device=self.device) * self.fps / self.env_fps
            if (times < 0).any() or (times > len(joints) - 1 + 1.e-5).any():
                raise ValueError('Task AMP window would cross a clip boundary')
            times = times.clamp(max=len(joints)-1)
            lo = times.floor().long(); hi = (lo+1).clamp(max=len(joints)-1)
            weight = (times-lo).unsqueeze(-1)
            def blend(v):
                w = weight.unsqueeze(-1) if v.ndim == 3 else weight
                return v[lo]*(1-w)+v[hi]*w
            q0, q1 = quat[lo], quat[hi]
            q1 = torch.where((q0*q1).sum(-1, keepdim=True) < 0, -q1, q1)
            q = torch.nn.functional.normalize(q0*(1-weight)+q1*weight, dim=-1)
            result[mask] = pack_task_frame(blend(joints), q, blend(ends), blend(linear), blend(angular), blend(box))
        return result.flatten(1)
