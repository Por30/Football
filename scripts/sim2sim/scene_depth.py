"""CPU scene depth from visible MuJoCo surfaces, with the v5 camera convention.

Native ray queries use the original mesh triangles and current geom poses. A
model copy changes only perception groups; the live physics model is untouched.
"""
import copy
import importlib.util
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE = ROOT/'docs/agilekickball_v5/camera_unitree_g1_d435i.json'
# This helper has no simulator imports. Loading the file avoids the package's
# IsaacSim environment registration in this standalone CPU runner.
_spec = importlib.util.spec_from_file_location('kickball_depth_contract',
    ROOT/'source/perceptual_ball/perceptual_ball/kickball_depth.py')
camera_contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(camera_contract)


def select_profile(mode, source_contract, profile_path=None):
    if mode not in ('scene', 'analytic'):
        raise ValueError('Unknown depth mode: '+str(mode))
    if source_contract is not None:
        if mode != 'scene' or not isinstance(source_contract, dict):
            raise ValueError('Scene-depth export requires scene mode and a valid depth contract')
        profile = camera_contract.validate_profile(copy.deepcopy(source_contract.get('profile')), allow_subpolicy_capture=True)
        expected = camera_contract.depth_contract(profile)
        if any(source_contract.get(k) != v for k, v in expected.items()):
            raise ValueError('Unsupported or inconsistent exported scene-depth contract')
        if profile_path is not None and camera_contract.load_profile(profile_path, allow_subpolicy_capture=True) != profile:
            raise ValueError('Camera profile differs from the exported policy contract')
        return profile
    if mode == 'analytic':
        if profile_path is not None:
            raise ValueError('Camera profiles apply only to scene depth')
        return None
    return camera_contract.load_profile(profile_path or DEFAULT_PROFILE, allow_subpolicy_capture=True)


class SceneDepthCamera:
    def __init__(self, model, profile, robot_root=None):
        self.profile = copy.deepcopy(camera_contract.validate_profile(profile, allow_subpolicy_capture=True))
        self.parent = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, profile['parent_link'])
        if self.parent < 0:
            raise ValueError('Camera parent link is absent from MuJoCo model')
        self.robot_bodies = set()
        if robot_root is not None:
            for body in range(model.nbody):
                ancestor = body
                while ancestor and ancestor != robot_root:
                    ancestor = int(model.body_parentid[ancestor])
                if ancestor == robot_root:
                    self.robot_bodies.add(body)
        material = model.geom_matid
        alpha = model.geom_rgba[:, 3].copy()
        assigned = material >= 0
        alpha[assigned] = model.mat_rgba[material[assigned], 3]
        self.visible_geoms = alpha > 0
        noncontact = (model.geom_contype == 0) & (model.geom_conaffinity == 0)
        self.collision_only_bodies = []
        for body in self.robot_bodies:
            geoms = model.geom_bodyid == body
            if np.any(geoms & noncontact & self.visible_geoms):
                self.visible_geoms[geoms & ~noncontact] = False
            elif np.any(geoms & self.visible_geoms):
                self.collision_only_bodies.append(body)
        self.model = copy.copy(model)
        self.model.geom_group[:] = np.where(self.visible_geoms, 0, 5)
        self.groups = np.array([1, 0, 0, 0, 0, 0], dtype=np.uint8)
        # The model copy has identical geom/mesh/BVH indices; data comes from
        # mj_forward on the live model, including articulated and free bodies.
        np.testing.assert_array_equal(self.model.geom_bodyid, model.geom_bodyid)
        np.testing.assert_array_equal(self.model.geom_dataid, model.geom_dataid)
        fx, fy, cx, cy = camera_contract.target_intrinsics(profile)
        v, u = np.mgrid[:profile['height'], :profile['width']]
        rays = np.stack((np.ones_like(u), -(u-cx)/fx, -(v-cy)/fy), -1).reshape(-1, 3)
        self.rays = np.ascontiguousarray(rays/np.linalg.norm(rays, axis=-1, keepdims=True))
        self.cosine = self.rays[:, 0]
        rotation = np.empty(9)
        mujoco.mju_quat2Mat(rotation, np.asarray(profile['quaternion_wxyz_world'], dtype=float))
        self.offset_rotation = rotation.reshape(3, 3)
        self.near, self.far = profile['near_m'], profile['far_m']
        self.capture_events = []
        self.policy_samples = []
        self._latest_event_index = None
        self.reset()

    def reset(self):
        if self._latest_event_index is not None:
            event = self.capture_events[self._latest_event_index]
            if not event['consumed']:
                event['discarded_on_reset'] = True
        self.latest = None
        self.capture_time_s = None
        self.capture_count = 0
        self.phase_start_s = None
        self.next_capture_index = 0
        self._latest_event_index = None
        self.hit_geoms = np.full(len(self.rays), -1, dtype=np.int32)

    def is_due(self, time_s):
        return (self.latest is None or
                time_s >= self.phase_start_s+self.next_capture_index*self.profile['update_period_s']-1.e-9)

    def consume(self, data):
        """50 Hz policy consumes only an actually captured, nonfuture frame."""
        frame = self.sample(data)
        age = float(data.time)-self.capture_time_s
        if age < -1.e-9:
            raise ValueError('Policy attempted to consume a future camera frame')
        self.capture_events[self._latest_event_index]['consumed'] = True
        self.policy_samples.append(dict(policy_time_s=float(data.time), capture_event_index=self._latest_event_index,
                                        capture_time_s=self.capture_time_s, frame_age_s=max(0., age)))
        return frame

    def pose(self, data):
        parent_rotation = data.xmat[self.parent].reshape(3, 3)
        position = data.xpos[self.parent]+parent_rotation@self.profile['position_m']
        rotation = parent_rotation@self.offset_rotation
        if not np.isfinite(position).all() or not np.isfinite(rotation).all():
            raise ValueError('Nonfinite scene camera pose')
        return position, rotation

    def sample(self, data):
        now = float(data.time)
        if not np.isfinite(now):
            raise ValueError('Nonfinite camera timestamp')
        if self.capture_time_s is not None:
            if now < self.capture_time_s-1.e-9:
                raise ValueError('Camera time moved backwards without reset')
            if not self.is_due(now):
                return self.latest.copy()
        if self.phase_start_s is None:
            self.phase_start_s = now
        period = self.profile['update_period_s']
        index = max(self.next_capture_index, int(np.floor((now-self.phase_start_s+1.e-9)/period)))
        scheduled = self.phase_start_s+index*period
        skipped = index-self.next_capture_index
        position, rotation = self.pose(data)
        directions = np.ascontiguousarray(self.rays@rotation.T)
        distances = np.empty(len(self.rays))
        ids = np.full(len(self.rays), -1, dtype=np.int32)
        # cutoff is range, not optical Z; off-axis ranges can exceed far.
        mujoco.mj_multiRay(self.model, data, position, directions.ravel(), self.groups,
                          1, -1, ids, distances, len(self.rays), self.far/self.cosine.min())
        # Match v5: the query starts at each pixel's near plane. A surface
        # before it must not hide a valid surface behind it (including an exit).
        before_near = (distances >= 0) & (distances*self.cosine < self.near)
        for pixel in np.flatnonzero(before_near):
            offset = self.near/self.cosine[pixel]
            geom = np.array([-1], dtype=np.int32)
            distance = mujoco.mj_ray(self.model, data, position+offset*directions[pixel],
                                    directions[pixel], self.groups, 1, -1, geom)
            distances[pixel] = offset+distance if distance >= 0 else -1
            ids[pixel] = geom[0]
        depth = distances*self.cosine
        valid = (distances >= 0) & (depth <= self.far)
        self.hit_geoms = np.where(valid, ids, -1).astype(np.int32)
        depth = np.where(valid, depth, self.far).clip(self.near, self.far)
        if not np.isfinite(depth).all():
            raise ValueError('Nonfinite scene depth')
        self.latest = depth.reshape(self.profile['height'], self.profile['width']).astype(np.float32)
        self.capture_time_s = now
        self.capture_count += 1
        if self._latest_event_index is not None:
            previous = self.capture_events[self._latest_event_index]
            if not previous['consumed']:
                previous['overwritten_before_consumption'] = True
        self.capture_events.append(dict(scheduled_time_s=scheduled, actual_time_s=now,
            quantization_delay_s=max(0., now-scheduled), missed_scheduled_frames=skipped, consumed=False,
            overwritten_before_consumption=False, discarded_on_reset=False))
        self._latest_event_index = len(self.capture_events)-1
        self.next_capture_index = index+1
        return self.latest.copy()

    def metadata(self):
        return dict(backend='mujoco_native_visible_surface_ray_cast', output='optical_z_metres',
                    geometry='visible_mjcf_geoms_robot_visual_meshes_and_all_environment',
                    profile=self.profile, target_intrinsics=list(camera_contract.target_intrinsics(self.profile)),
                    normalization='none', history_order='oldest_to_newest',
                    visible_geom_ids=np.flatnonzero(self.visible_geoms).tolist(),
                    excluded_geom_ids=np.flatnonzero(~self.visible_geoms).tolist(),
                    collision_only_robot_body_ids=self.collision_only_bodies,
                    calibration_status=self.profile['calibration_status'])
