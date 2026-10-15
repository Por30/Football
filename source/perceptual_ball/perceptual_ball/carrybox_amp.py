"""FindBox motion schema: 60 Hz PhysHSI data -> 50 Hz proprioceptive AMP windows.

No object, world position, root linear velocity or end-effector truth enters AMP.
Source provenance and immutable clip hashes are in assets/motions/findbox/amp_manifest.json.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import torch
from isaaclab.utils.math import quat_apply_inverse, quat_mul, quat_conjugate, axis_angle_from_quat

AMP_WINDOW = 10
AMP_FRAME_DIM = 64
DEFAULT_DATASET_PATH = str(Path(__file__).resolve().parent / 'assets/motions/findbox')
DIRECTORY_GROUPS = {'locomotion': 'loco_direction', 'pick_up': 'pickUp', 'hold': 'carryWith',
                    'loco_direction': 'loco_direction', 'pickUp': 'pickUp', 'carryWith': 'carryWith'}
SOURCE_JOINT_NAMES = tuple(
    [f'{side}_{part}_joint' for side in ('left', 'right') for part in
     ('hip_pitch', 'hip_roll', 'hip_yaw', 'knee', 'ankle_pitch', 'ankle_roll')]
    + ['waist_yaw_joint', 'waist_roll_joint', 'waist_pitch_joint']
    + [f'{side}_{part}_joint' for side in ('left', 'right') for part in
       ('shoulder_pitch', 'shoulder_roll', 'shoulder_yaw', 'elbow', 'wrist_roll', 'wrist_pitch', 'wrist_yaw')]
)


def pack_frame(joint_pos, joint_vel, gravity, angular_velocity):
    """Unscaled radians, rad/s and unit gravity direction; discriminator owns normalization."""
    return torch.cat((joint_pos, joint_vel, gravity, angular_velocity), dim=-1)


def joint_mapping(robot_joint_names):
    if len(robot_joint_names) != 29 or set(robot_joint_names) != set(SOURCE_JOINT_NAMES):
        raise ValueError('FindBox AMP requires the exact named 29-DOF G1 joint set')
    return [robot_joint_names.index(name) for name in SOURCE_JOINT_NAMES]


def resolve_dataset_path(path=None):
    if path is None:
        path = DEFAULT_DATASET_PATH
    path = Path(path).expanduser()
    return path if path.is_absolute() else Path(__file__).resolve().parents[3] / path


def clip_group(row):
    """Keep AMP/RSI skill names independent of normalized directory spelling."""
    relative = Path(row['file'])
    if relative.is_absolute() or '..' in relative.parts or len(relative.parts) != 2:
        raise ValueError('Invalid FindBox clip path')
    group = row.get('group', relative.parts[0])
    if DIRECTORY_GROUPS.get(relative.parts[0]) != group:
        raise ValueError('Invalid FindBox clip group/directory')
    return group


class FindBoxMotionLibrary:
    def __init__(self, dataset_path=None, device='cpu', env_fps=50., window_length=AMP_WINDOW):
        self.device = device
        self.env_fps = float(env_fps)
        self.window_length = window_length
        root = resolve_dataset_path(dataset_path)
        self.root = root
        raw_manifest = (root / 'amp_manifest.json').read_bytes()
        manifest = json.loads(raw_manifest)
        if (manifest.get('schema') != 1 or manifest.get('fps') != 60
                or manifest.get('quaternion_order') != 'xyzw'
                or manifest.get('joint_names') != list(SOURCE_JOINT_NAMES)):
            raise ValueError('Unsupported FindBox schema, fps, quaternion or joint order')
        if not math.isfinite(self.env_fps) or self.env_fps <= 0 or window_length < 2:
            raise ValueError('Invalid AMP sample rate/window')
        groups = manifest['groups']
        if (set(groups) != {'loco_direction', 'pickUp', 'carryWith'}
                or any(not math.isfinite(w) or w <= 0 for w in groups.values())):
            raise ValueError('FindBox group weights must be finite and positive')
        self.fps = float(manifest['fps'])
        self.metadata = dict(schema=1, manifest_sha256=hashlib.sha256(raw_manifest).hexdigest(),
                             fps=self.fps, env_fps=self.env_fps, window_length=window_length,
                             feature_schema='joint_pos29_joint_vel29_gravity3_angvel3', groups=groups)
        self.clips, self.clip_names, self.clip_groups, self.weights = [], [], [], []
        rows = manifest['clips']
        row_groups = [clip_group(row) for row in rows]
        group_counts = {g: row_groups.count(g) for g in groups}
        if not rows or not all(group_counts.values()) or len({row['file'] for row in rows}) != len(rows):
            raise ValueError('FindBox manifest requires distinct clips and all three motion groups')
        for row, group in zip(rows, row_groups):
            relative = Path(row['file'])
            path = root / relative
            if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
                raise ValueError(f'FindBox clip hash mismatch: {relative}')
            data = torch.load(path, map_location='cpu', weights_only=True)
            n = row['frames']
            for key, shape in (('joint_position', (n, 29)), ('base_quat', (n, 4))):
                value = data.get(key)
                if not isinstance(value, torch.Tensor) or value.shape != shape or not torch.isfinite(value).all():
                    raise ValueError(f'Invalid FindBox {key}: {relative}')
            if n < 2 or n - 1 < (window_length - 1) * self.fps / self.env_fps:
                raise ValueError(f'FindBox clip too short for complete AMP window: {relative}')
            joints = data['joint_position'].float().to(device)
            quat = data['base_quat'][:, [3, 0, 1, 2]].float().to(device)
            norms = quat.norm(dim=-1, keepdim=True)
            if not torch.all((norms - 1).abs() < .01):
                raise ValueError(f'Invalid FindBox quaternion norm: {relative}')
            quat = quat / norms
            velocity = torch.empty_like(joints)
            velocity[:-1] = (joints[1:] - joints[:-1]) * self.fps
            velocity[-1] = velocity[-2]
            delta = quat_mul(quat_conjugate(quat[:-1]), quat[1:])
            # q and -q denote the same pose. Use the shortest relative axis-angle.
            delta = torch.where(delta[:, :1] < 0, -delta, delta)
            angular = torch.empty((n, 3), device=device)
            angular[:-1] = axis_angle_from_quat(delta) * self.fps
            angular[-1] = angular[-2]
            self.clips.append((joints, velocity, quat, angular))
            self.clip_names.append(str(relative))
            self.clip_groups.append(group)
            self.weights.append(groups[group] / group_counts[group])
        self.weights = torch.tensor(self.weights, device=device)
        self.weights /= self.weights.sum()
        self.lengths = torch.tensor([len(c[0]) for c in self.clips], device=device)
        self.num_clips = len(self.clips)
        self.metadata['clip_count'] = self.num_clips
        self.metadata['total_frames'] = int(self.lengths.sum())

    def sample_expert_amp_obs(self, batch_size, return_clip_ids=False):
        ids = torch.multinomial(self.weights, batch_size, replacement=True)
        span = (self.window_length - 1) * self.fps / self.env_fps
        starts = torch.rand(batch_size, device=self.device) * (self.lengths[ids] - 1 - span)
        windows = self.windows(ids, starts)
        return (windows, ids) if return_clip_ids else windows

    def windows(self, clip_ids, native_starts):
        """Interpolate each clip independently; never cross clip or reset boundaries."""
        result = torch.empty((len(clip_ids), self.window_length, AMP_FRAME_DIM), device=self.device)
        if (not torch.isfinite(native_starts).all() or (clip_ids < 0).any() or (clip_ids >= self.num_clips).any()):
            raise ValueError('Invalid AMP window request')
        for clip_id in clip_ids.unique().tolist():
            mask = clip_ids == clip_id
            joints, velocity, quat, angular = self.clips[clip_id]
            times = native_starts[mask, None] + torch.arange(self.window_length, device=self.device) * self.fps / self.env_fps
            if (times < 0).any() or (times > len(joints) - 1 + 1.e-5).any():
                raise ValueError('AMP window would cross a clip boundary')
            times = times.clamp(max=len(joints) - 1)
            floor = times.floor().long()
            ceil = (floor + 1).clamp(max=len(joints) - 1)
            weight = (times - floor).unsqueeze(-1)
            def blend(value):
                return value[floor] * (1 - weight) + value[ceil] * weight
            q0, q1 = quat[floor], quat[ceil]
            q1 = torch.where((q0 * q1).sum(-1, keepdim=True) < 0, -q1, q1)
            q = torch.nn.functional.normalize(q0 * (1 - weight) + q1 * weight, dim=-1)
            gravity = torch.zeros_like(q[..., :3]); gravity[..., 2] = -1.
            gravity = quat_apply_inverse(q.reshape(-1, 4), gravity.reshape(-1, 3)).reshape(*q.shape[:-1], 3)
            result[mask] = pack_frame(blend(joints), blend(velocity), gravity, blend(angular))
        return result.flatten(1)
