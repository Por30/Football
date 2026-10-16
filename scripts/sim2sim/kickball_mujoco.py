#!/usr/bin/env python3
"""CPU-only Kickball sim2sim with scene depth. No DDS or real-robot commands.

Uses the official G1 MJCF with a local ball/floor/head-frame adaptation.
Scene depth includes visible robot meshes and all environment surfaces. The
historical v4 ball-only input is available with --depth-mode analytic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scene_depth import SceneDepthCamera, select_profile

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'logs/rsl_rl/agilekickball_v4/2026-10-12_13-48-41_return_to_sender_20261012_v3init'
ROBOT_XML = Path('/home/cao/unitree_mujoco/unitree_robots/g1/g1_29dof.xml')
TERM_DIMS = (3, 3, 29, 29, 15, 29)
END_EFFECTORS = ('left_wrist_roll_link', 'right_wrist_roll_link',
                 'left_ankle_pitch_link', 'right_ankle_pitch_link')
CAM_POS = np.array([.0576235, .01753, .42987])
CAM_QUAT = np.array([.2557, -.6593, .6593, -.2557])


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def quat_matrix(q):
    # Same unit-quaternion formula as IsaacLab quat_apply; preserve v4 constants.
    w, x, y, z = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def ray_grid():
    v, u = np.mgrid[:27, :48].astype(np.float32)
    focal = 27 / (2 * math.tan(math.radians(58) / 2))
    rays = np.stack(((u-24)/focal, (v-13.5)/focal, np.ones_like(u)), -1)
    return rays / np.linalg.norm(rays, axis=-1, keepdims=True)


RAYS = ray_grid()


def ball_depth(center, rays=RAYS):
    center = np.asarray(center, dtype=np.float32)
    along = rays @ center
    disc = .11**2 - (center @ center - along**2)
    near = along - np.sqrt(np.maximum(disc, 0))
    return np.where((disc >= 0) & (near > .1) & (near < 3), near, 3).astype(np.float32)


def policy_depth(torso_position, torso_quaternion, ball_position):
    """Match v4's float32 world-camera quat_mul -> quat_inv -> quat_apply.

    The saved camera quaternion is slightly nonunit. Normalizing it or using
    a rotation-matrix transpose changes the trained silhouette at edge pixels.
    Quaternion arithmetic follows IsaacLab utils.math (BSD-3-Clause).
    """
    position = torch.as_tensor(torso_position,dtype=torch.float32)
    q = torch.as_tensor(torso_quaternion,dtype=torch.float32)
    ball = torch.as_tensor(ball_position,dtype=torch.float32)

    def apply(quat, vector):
        t = torch.linalg.cross(quat[1:],vector)*2
        return vector+quat[0]*t+torch.linalg.cross(quat[1:],t)

    cam_pos = position+apply(q,torch.as_tensor(CAM_POS,dtype=torch.float32))
    w1,x1,y1,z1 = q.unbind()
    w2,x2,y2,z2 = torch.as_tensor(CAM_QUAT,dtype=torch.float32).unbind()
    ww = (z1+x1)*(x2+y2)
    yy = (w1-y1)*(w2+z2)
    zz = (w1+y1)*(w2-z2)
    xx = ww+yy+zz
    qq = .5*(xx+(z1-x1)*(x2-y2))
    cam_q = torch.stack((qq-ww+(z1-y1)*(y2-z2),qq-xx+(x1+w1)*(x2+w2),
                         qq-yy+(w1-x1)*(y2+z2),qq-zz+(z1+y1)*(w2-x2)))
    inverse = cam_q*torch.tensor([1.,-1.,-1.,-1.])/cam_q.square().sum().clamp(min=1.e-9)
    center = apply(inverse,ball-cam_pos)
    return ball_depth(center.numpy())


class History:
    def __init__(self):
        self.terms = None
        self.depth = None

    def append(self, terms, depth):
        if tuple(np.asarray(t).size for t in terms) != TERM_DIMS or depth.shape != (27, 48):
            raise ValueError('Invalid observation shape')
        if not all(np.isfinite(t).all() for t in [*terms, depth]):
            raise ValueError('Nonfinite observation')
        if self.terms is None:
            self.terms = [np.repeat(np.asarray(t, np.float32)[None], 8, axis=0) for t in terms]
            self.depth = np.repeat(depth[None], 8, axis=0)
        else:
            for hist, term in zip(self.terms, terms):
                hist[:-1] = hist[1:]
                hist[-1] = term
            self.depth[:-1] = self.depth[1:]
            self.depth[-1] = depth
        return np.concatenate([t.ravel() for t in self.terms])[None], self.depth[None].copy()


def make_scene(robot_xml, physics_dt):
    tree = ET.parse(robot_xml)
    root = tree.getroot()
    compiler = root.find('compiler')
    meshdir = Path(compiler.get('meshdir', 'meshes'))
    compiler.set('meshdir', str(meshdir if meshdir.is_absolute() else robot_xml.parent/meshdir))
    option = root.find('option')
    if option is None:
        option = ET.SubElement(root, 'option')
    option.set('timestep', str(physics_dt))
    option.set('integrator', 'implicitfast')
    world = root.find('worldbody')
    torso = world.find('.//body[@name="torso_link"]')
    if torso is None:
        raise ValueError('Official model has no torso_link')
    # Training URDF head_joint, not the visual head centre; no added mass.
    ET.SubElement(torso, 'site', name='kickball_head_frame', pos='.0039635 0 -.044', size='.001', rgba='0 0 0 0')
    # Match training's disabled robot self-collision; retain official geometry/inertia/limits.
    robot = world.find('.//body[@name="pelvis"]')
    if robot is None:
        raise ValueError('Official model has no pelvis body')
    for geom in robot.iter('geom'):
        if geom.get('contype', '1') != '0' or geom.get('conaffinity', '1') != '0':
            geom.set('contype', '1')
            geom.set('conaffinity', '2')
    ET.SubElement(world, 'light', pos='0 -3 4', dir='0 0 -1', directional='true')
    ET.SubElement(world, 'geom', name='kickball_floor', type='plane', size='20 20 .1',
                  rgba='.25 .35 .28 1', contype='2', conaffinity='3', friction='.6 .005 .0001')
    ball = ET.SubElement(world, 'body', name='kickball', pos='2 .15 .11')
    ET.SubElement(ball, 'freejoint', name='kickball_free')
    ET.SubElement(ball, 'geom', name='kickball_geom', type='sphere', size='.11', mass='.43',
                  rgba='.95 .9 .3 1', contype='2', conaffinity='3', friction='.5 .005 .0001')
    return ET.tostring(root, encoding='unicode')


def gains(names):
    pairs = []
    for name in names:
        if 'hip_' in name: pair = (150, 2)
        elif 'knee' in name or 'waist' in name: pair = (300, 4)
        elif 'ankle' in name: pair = (40, 1)
        elif 'shoulder' in name: pair = (200, 3)
        elif 'elbow' in name: pair = (100, 1)
        elif 'wrist' in name: pair = (20, .5)
        else: raise ValueError(f'Unknown joint gains: {name}')
        pairs.append(pair)
    return np.array(pairs).T


class KickballSim:
    def __init__(self, export_dir=RUN/'exported', robot_xml=ROBOT_XML, physics_dt=.002, speed=2.,
                 depth_mode='scene', camera_profile=None):
        self.export_dir, self.robot_xml = Path(export_dir), Path(robot_xml)
        self.manifest = json.loads((self.export_dir/'manifest.json').read_text())
        meta = self.manifest['metadata']
        if (self.manifest['flat_groups'] != ['proprio_hist'] or
                self.manifest['flat_group_dims'] != [864] or self.manifest['depth_shape'] != [8,27,48] or
                self.manifest['proprio_history_order'] != 'term_major_then_oldest_to_newest' or
                self.manifest['depth_order'] != 'oldest_to_newest' or
                not self.manifest.get('includes_ball_state_feedback')):
            raise ValueError('Unsupported Kickball observation/export contract')
        self.depth_mode = depth_mode
        source_contract = meta.get('depth_contract')
        profile = select_profile(depth_mode, source_contract, camera_profile)
        self.depth_distribution_shift = depth_mode == 'scene' and source_contract is None
        self.policy_training_depth = 'scene_optical_z' if source_contract is not None else 'v4_analytic_ball_only_ray_distance'
        self.control_dt = float(meta['control_dt'])
        self.substeps = round(self.control_dt / physics_dt)
        if physics_dt <= 0 or self.substeps < 1 or not np.isclose(self.substeps*physics_dt, self.control_dt):
            raise ValueError('control_dt must be a positive integer multiple of physics_dt')
        if not np.isclose(self.control_dt, .02) or not np.isfinite(speed) or speed <= 0:
            raise ValueError('Expected 50 Hz policy and positive finite serve speed')
        self.scene_xml = make_scene(self.robot_xml, physics_dt)
        self.model = mujoco.MjModel.from_xml_string(self.scene_xml)
        self.data = mujoco.MjData(self.model)
        names = meta['joint_names']
        if len(names) != 29 or len(set(names)) != 29:
            raise ValueError('Expected 29 unique policy joints')
        self.joints = np.array([self.id(mujoco.mjtObj.mjOBJ_JOINT, n) for n in names])
        self.qadr = self.model.jnt_qposadr[self.joints]
        self.vadr = self.model.jnt_dofadr[self.joints]
        ids = []
        for j in self.joints:
            found = np.flatnonzero(self.model.actuator_trnid[:, 0] == j)
            if len(found) != 1:
                raise ValueError('Joint must have exactly one actuator')
            ids.append(found[0])
        self.actuators = np.array(ids)
        self.limits = self.model.actuator_ctrlrange[self.actuators].copy()
        for k, j in enumerate(self.joints):
            if not self.model.actuator_ctrllimited[self.actuators[k]]:
                raise ValueError('Finite actuator limits required')
            if self.model.jnt_actfrclimited[j]:
                self.limits[k,0] = max(self.limits[k,0], self.model.jnt_actfrcrange[j,0])
                self.limits[k,1] = min(self.limits[k,1], self.model.jnt_actfrcrange[j,1])
        if not np.isfinite(self.limits).all() or np.any(self.limits[:,0] >= self.limits[:,1]):
            raise ValueError('Invalid torque bounds')
        self.default = np.asarray(meta['default_joint_positions'])
        self.offset = np.asarray(meta['action_offset'])
        self.scale, self.clip = float(meta['action_scale']), meta['clip_actions']
        if self.default.shape != (29,) or self.offset.shape != (29,) or not np.isfinite([*self.default,*self.offset,self.scale]).all():
            raise ValueError('Invalid action metadata')
        self.kp, self.kd = gains(names)
        self.pelvis = self.id(mujoco.mjtObj.mjOBJ_BODY, 'pelvis')
        self.torso = self.id(mujoco.mjtObj.mjOBJ_BODY, 'torso_link')
        self.ends = [self.id(mujoco.mjtObj.mjOBJ_BODY,n) for n in END_EFFECTORS]
        self.feet = [self.id(mujoco.mjtObj.mjOBJ_BODY,n) for n in
                     ('left_ankle_roll_link','right_ankle_roll_link')]
        self.head_site = self.id(mujoco.mjtObj.mjOBJ_SITE, 'kickball_head_frame')
        self.ball_body = self.id(mujoco.mjtObj.mjOBJ_BODY, 'kickball')
        bj = self.id(mujoco.mjtObj.mjOBJ_JOINT, 'kickball_free')
        self.bq, self.bv = self.model.jnt_qposadr[bj], self.model.jnt_dofadr[bj]
        self.ball_geom = self.id(mujoco.mjtObj.mjOBJ_GEOM, 'kickball_geom')
        self.floor_geom = self.id(mujoco.mjtObj.mjOBJ_GEOM, 'kickball_floor')
        self.camera = SceneDepthCamera(self.model, profile, self.pelvis) if depth_mode == 'scene' else None
        if self.camera is not None and physics_dt > profile['update_period_s']+1.e-9:
            raise ValueError('physics_dt exceeds the camera capture period')
        self.speed = speed
        torch.set_num_threads(1)
        self.policy = torch.jit.load(str(self.export_dir/'policy.pt'), map_location='cpu').eval()
        self.reset()

    def id(self, kind, name):
        result = mujoco.mj_name2id(self.model, kind, name)
        if result < 0:
            raise ValueError(f'Model missing {name}')
        return result

    def reset(self):
        elapsed = self.data.time
        mujoco.mj_resetData(self.model, self.data)
        self.data.time = elapsed
        self.data.qpos[:7] = [0,0,.8,1,0,0,0]
        self.data.qpos[self.qadr] = self.default
        self.last_action = np.zeros(29, dtype=np.float32)
        self.history = History()
        if self.camera is not None:
            self.camera.reset()
        self.serve()

    def serve(self):
        # Deterministic rolling serve; independent of training's randomized curriculum.
        self.data.qpos[self.bq:self.bq+7] = [2,.15,.11,1,0,0,0]
        self.data.qvel[self.bv:self.bv+6] = [-self.speed,0,0,0,-self.speed/.11,0]
        self.ball_active = True
        self.wait_elapsed = self.stable_elapsed = 0.
        mujoco.mj_forward(self.model,self.data)

    def set_ball_speed(self, speed, apply_now=False):
        """Set future serves; optionally change only the current ball's rolling speed."""
        if not np.isfinite(speed) or speed <= 0:
            raise ValueError('Ball speed must be positive and finite')
        self.speed = float(speed)
        if apply_now:
            velocity = self.data.qvel[self.bv:self.bv+6]
            current = np.linalg.norm(velocity[:2])
            direction = velocity[:2]/current if current > 1e-6 else np.array([-1.,0.])
            velocity[:2] = direction*self.speed
            # Free-joint translation is world-frame, angular velocity is body-frame.
            rotation = quat_matrix(self.data.qpos[self.bq+3:self.bq+7])
            spin_z = (rotation @ velocity[3:])[2]
            velocity[3:] = rotation.T @ [-velocity[1]/.11,velocity[0]/.11,spin_z]
            mujoco.mj_forward(self.model,self.data)

    def apply_ball_command(self, action, speed):
        if action not in ('set','apply','serve'):
            raise ValueError(f'Unknown ball command: {action}')
        self.set_ball_speed(speed,apply_now=action == 'apply')
        if action == 'serve':
            self.serve()

    def balanced(self):
        d = self.data
        gravity = d.xmat[self.pelvis].reshape(3,3).T @ [0,0,-1]
        feet_z = d.xpos[self.feet,2]
        return bool(np.linalg.norm(gravity[:2]) < .15 and gravity[2] < -.98
                and np.linalg.norm(d.qvel[:3]) < .25 and np.linalg.norm(d.qvel[3:6]) < .5
                and .7 < d.qpos[2] < .9 and np.isfinite(d.qvel[self.vadr]).all()
                and np.all(feet_z < .12) and np.all(feet_z > -.03))

    def advance_round(self):
        """Training's ball-end/recovery gate; deterministic serve geometry, no curriculum."""
        pos = self.data.xpos[self.ball_body]
        velocity = self.data.qvel[self.bv:self.bv+2]
        if self.ball_active:
            if np.linalg.norm(pos[:2]) > 3 or pos[0] < -.3 or np.linalg.norm(velocity) < .15:
                self.ball_active = False
                self.wait_elapsed = self.stable_elapsed = 0.
            return None
        self.wait_elapsed += self.control_dt
        self.stable_elapsed = self.stable_elapsed+self.control_dt if self.balanced() else 0.
        if self.wait_elapsed >= 5:
            self.reset()
            return 'recovery_timeout'
        if self.wait_elapsed >= .4 and self.stable_elapsed >= .3:
            self.serve()
            return 'recovered_serve'
        return None

    def observe(self):
        d, m = self.data, self.model
        rotation = d.xmat[self.pelvis].reshape(3,3)
        vel = np.zeros(6)
        # mjOBJ_BODY local axes are the inertial frame, not the pelvis link.
        mujoco.mj_objectVelocity(m,d,mujoco.mjtObj.mjOBJ_BODY,self.pelvis,vel,0)
        positions = np.vstack((d.xpos[self.ends], d.site_xpos[self.head_site]))
        relative = (positions - d.xpos[self.pelvis]) @ rotation
        terms = [rotation.T @ vel[:3], rotation.T @ [0,0,-1], d.qpos[self.qadr]-self.default,
                 d.qvel[self.vadr], relative.ravel(), self.last_action]
        depth = (self.camera.consume(d) if self.camera is not None else
                 policy_depth(d.xpos[self.torso],d.xquat[self.torso],d.xpos[self.ball_body]))
        flat, stack = self.history.append(terms,depth)
        return flat, stack

    def capture_depth_at_physics_tick(self):
        if self.camera is not None and self.camera.is_due(float(self.data.time)):
            # mj_step integrates qpos after its forward pass. Refresh only
            # kinematics for the sensor; do not change physics dt or state.
            mujoco.mj_kinematics(self.model, self.data)
            self.camera.sample(self.data)

    def target(self, action):
        action = np.asarray(action, dtype=np.float32)
        if action.shape != (29,) or not np.isfinite(action).all():
            raise ValueError('Invalid policy action; simulation stopped')
        if self.clip is not None:
            action = np.clip(action,-self.clip,self.clip)
        self.last_action = action.copy()
        return self.offset + self.scale*action

    def torque(self, target):
        raw = self.kp*(target-self.data.qpos[self.qadr])-self.kd*self.data.qvel[self.vadr]
        if not np.isfinite(raw).all():
            raise ValueError('Nonfinite PD torque')
        bounded = np.clip(raw,self.limits[:,0],self.limits[:,1])
        return bounded, int(np.count_nonzero(raw != bounded))


def run(args):
    summary = {'interface_smoke_pass': False, 'stable_for_full_duration': False,
               'real_vision_validated': False, 'real_robot_validated': False,
               'depth_mode': getattr(args,'depth_mode','scene'), 'steps': 0, 'falls': 0,
               'ball_robot_contact_steps': 0, 'visible_frames': 0, 'torque_saturated_joint_steps': 0,
               'valid_depth_frames': 0, 'depth_captures': 0,
               'depth_capture_times_s': [], 'history_sample_period_s': .02,
               'target_outside_joint_range_count': 0, 'serves': 1, 'errors': [],
               'ball_speed_commands': [], 'manual_serves': 0,
               'max_root_displacement_m': 0., 'travel_limit_exceeded_steps': 0,
               'recovery_timeouts': 0, 'recovered_serves': 0, 'serve_mode': args.serve_mode,
               'physics_dt': args.physics_dt, 'training_physics_dt': .005,
               'torch_version': torch.__version__, 'mujoco_version': mujoco.__version__}
    viewer = None
    depth_window = None
    sim = None
    timings, heights, trace = [], [], []
    depth_samples = []
    try:
        if not np.isfinite(args.duration) or args.duration <= 0:
            raise ValueError('Duration must be positive and finite')
        sim = KickballSim(args.export_dir,args.robot_xml,args.physics_dt,args.speed,
                         getattr(args,'depth_mode','scene'),getattr(args,'camera_profile',None))
        d, m = sim.data, sim.model
        total = round(args.duration/sim.control_dt)
        if total < 1:
            raise ValueError('Duration shorter than one control step')
        summary.update(control_dt=sim.control_dt, requested_steps=total,
                       depth_distribution_shift=sim.depth_distribution_shift,
                       policy_training_depth=sim.policy_training_depth,
                       depth_semantics='optical_z_metres' if sim.camera is not None else 'ray_distance_metres',
                       runtime_depth_contract=sim.camera.metadata() if sim.camera is not None else None,
                       source_depth_contract=sim.manifest['metadata'].get('depth_contract'),
                       depth_profile_matches_export=(True if sim.camera is not None and not sim.depth_distribution_shift else None),
                       policy_sha256=sha256(args.export_dir/'policy.pt'),
                       manifest_sha256=sha256(args.export_dir/'manifest.json'),
                       source_model_sha256=sha256(args.robot_xml),
                       scene_sha256=hashlib.sha256(sim.scene_xml.encode()).hexdigest(),
                       robot_mass_kg=float(m.body_mass.sum()-.43),
                       model_changes=['floor and .43kg/.11m ball', 'training head frame site',
                                      'robot self-collision disabled; official inertia/friction/torque bounds retained'],
                       known_training_model_differences={'mass_kg': [33.341,35.112142],
                           'hip_roll_effort_Nm': [139,88], 'ankle_and_waist_roll_pitch_effort_Nm': [35,50],
                           'waist_pitch_range_rad': [[-.62,.62],[-.52,.52]],
                           'note': 'training then official; waist frames, passive friction, foot contacts and restitution also differ'},
                       torque_limits=sim.limits.tolist(), joint_names=sim.manifest['metadata']['joint_names'])
        if sim.camera is not None:
            # Scene hits include the ground/body; they are not ball visibility.
            summary.pop('visible_frames')
            summary['depth_hit_pixel_steps'] = dict(robot=0, ground=0, ball=0, environment=0)
        if sim.depth_distribution_shift:
            print('Scene optical depth enabled. Loaded v4 weights were trained on ball-only ray depth; '
                  'this run has an input distribution shift and is a diagnostic.', file=sys.stderr)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.with_suffix('.xml').write_text(sim.scene_xml)
        if not args.headless:
            from mujoco import viewer as mjviewer
            viewer = mjviewer.launch_passive(m,d)
            viewer.cam.distance = 3.5
            viewer.cam.lookat[:] = [0,0,.7]
            if not args.no_depth_window:
                from depth_visualization import LiveDepthWindow
                depth_window = LiveDepthWindow(speed=sim.speed)
                depth_window.set_depth_mode(sim.depth_mode)
        start = time.perf_counter()
        for i in range(total):
            if viewer is not None and not viewer.is_running():
                raise RuntimeError('Viewer closed before requested duration')
            if depth_window is not None:
                depth_window.poll()
                for command, speed in depth_window.take_commands():
                    sim.apply_ball_command(command,speed)
                    summary['ball_speed_commands'].append({'time_s':float(d.time),
                        'action':command,'speed_m_s':speed})
                    if command == 'serve':
                        summary['serves'] += 1
                        summary['manual_serves'] += 1
            flat, depth = sim.observe()
            if sim.camera is None:
                summary['depth_captures'] += 1
                summary['depth_capture_times_s'].append(float(d.time))
            if depth_window is not None:
                if i % 5 == 0:
                    depth_window.update_speed(sim.speed,float(np.linalg.norm(d.qvel[sim.bv:sim.bv+2])))
                    depth_window.update(depth[0],float(d.time))
            if args.depth_output is not None and i % 5 == 0:
                # Copy the exact network input before stepping; never call observe twice.
                depth_samples.append((float(d.time),depth[0].copy()))
            valid_depth = int(np.any(depth[0,-1] < 3))
            summary['valid_depth_frames'] += valid_depth
            if sim.camera is None:
                summary['visible_frames'] += valid_depth
            else:
                for geom, count in zip(*np.unique(sim.camera.hit_geoms, return_counts=True)):
                    if geom < 0:
                        continue
                    category = ('ground' if geom == sim.floor_geom else 'ball' if geom == sim.ball_geom else
                                'robot' if int(m.geom_bodyid[geom]) in sim.camera.robot_bodies else 'environment')
                    summary['depth_hit_pixel_steps'][category] += int(count)
            t = time.perf_counter()
            with torch.inference_mode():
                action = sim.policy(torch.from_numpy(flat),torch.from_numpy(depth)).numpy()[0]
            timings.append((time.perf_counter()-t)*1000)
            target = sim.target(action)
            ranges = m.jnt_range[sim.joints]
            summary['target_outside_joint_range_count'] += int(np.count_nonzero((target<ranges[:,0])|(target>ranges[:,1])))
            contact = False
            for _ in range(sim.substeps):
                torque, saturated = sim.torque(target)
                summary['torque_saturated_joint_steps'] += saturated
                d.ctrl[sim.actuators] = torque
                mujoco.mj_step(m,d)
                if not np.isfinite(d.qpos).all() or not np.isfinite(d.qvel).all():
                    raise ValueError('MuJoCo nonfinite state')
                if any(w.number for w in d.warning):
                    raise ValueError('MuJoCo warning; refusing silent simulator recovery')
                sim.capture_depth_at_physics_tick()
                heights.append(float(d.qpos[2]))
                for c in d.contact:
                    if sim.ball_geom in (c.geom1,c.geom2) and sim.floor_geom not in (c.geom1,c.geom2):
                        contact = True
            mujoco.mj_forward(m,d)
            summary['ball_robot_contact_steps'] += int(contact)
            summary['steps'] += 1
            displacement = float(np.linalg.norm(d.qpos[:2]))
            summary['max_root_displacement_m'] = max(summary['max_root_displacement_m'],displacement)
            summary['travel_limit_exceeded_steps'] += int(displacement > .6)
            if i % 5 == 0:
                trace.append({'time_s': float(d.time), 'root_height_m': float(d.qpos[2]),
                              'root_xy': d.qpos[:2].tolist(),
                              'ball_xyz': d.xpos[sim.ball_body].tolist(),
                              'max_abs_action': float(np.abs(action).max())})
            if d.qpos[2] < .4:
                summary['falls'] += 1
                sim.reset()
                summary['serves'] += 1
            elif args.serve_mode == 'fixed' and (i+1) % 200 == 0:
                sim.serve()
                summary['serves'] += 1
            elif args.serve_mode == 'recovery':
                event = sim.advance_round()
                if event is not None:
                    summary['serves'] += 1
                    summary['recovery_timeouts' if event == 'recovery_timeout' else 'recovered_serves'] += 1
            if viewer is not None:
                viewer.sync()
                time.sleep(max(0,start+(i+1)*sim.control_dt-time.perf_counter()))
        summary['wall_time_s'] = time.perf_counter()-start
        summary['interface_smoke_pass'] = summary['steps'] == total
        summary['stable_for_full_duration'] = (summary['falls'] == 0 and min(heights) >= .4
                                               and summary['recovery_timeouts'] == 0 and sim.balanced()
                                               and summary['max_root_displacement_m'] <= .6)
        if args.depth_output is not None:
            from depth_visualization import export_depth_video
            summary['depth_visualization'] = export_depth_video(args.depth_output,depth_samples,depth_mode=sim.depth_mode)
    except Exception as exc:
        summary['interface_smoke_pass'] = False
        summary['errors'].append(f'{type(exc).__name__}: {exc}')
    finally:
        if sim is not None and sim.camera is not None:
            events = sim.camera.capture_events
            summary.update(depth_captures=len(events),
                depth_capture_times_s=[e['actual_time_s'] for e in events],
                depth_scheduled_capture_times_s=[e['scheduled_time_s'] for e in events],
                depth_capture_events=events, depth_policy_samples=sim.camera.policy_samples,
                depth_unique_consumed_frames=sum(e['consumed'] for e in events),
                depth_overwritten_before_consumption=sum(e['overwritten_before_consumption'] for e in events),
                depth_discarded_on_reset=sum(e['discarded_on_reset'] for e in events),
                depth_missed_scheduled_frames=sum(e['missed_scheduled_frames'] for e in events),
                depth_max_quantization_delay_s=max((e['quantization_delay_s'] for e in events), default=0.),
                depth_max_policy_frame_age_s=max((e['frame_age_s'] for e in sim.camera.policy_samples), default=0.))
        if depth_window is not None:
            summary['depth_window_frames'] = depth_window.frames
            depth_window.close()
        if viewer is not None:
            viewer.close()
        summary['min_root_height_m'] = min(heights) if heights else None
        summary['inference_ms_median'] = float(np.median(timings)) if timings else None
        summary['inference_ms_p99'] = float(np.percentile(timings,99)) if timings else None
        summary['trace'] = trace
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
        print(json.dumps({k:v for k,v in summary.items() if k not in
                          ('trace','torque_limits','joint_names','depth_capture_times_s',
                           'depth_scheduled_capture_times_s','depth_capture_events','depth_policy_samples')},indent=2))
    return 0 if summary['interface_smoke_pass'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-dir',type=Path,default=RUN/'exported')
    parser.add_argument('--robot-xml',type=Path,default=ROBOT_XML)
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--no-depth-window',action='store_true',help='Disable the live depth window (enabled by default with the MuJoCo viewer)')
    parser.add_argument('--duration',type=float,default=30.)
    parser.add_argument('--physics-dt',type=float,default=.002)
    parser.add_argument('--speed',type=float,default=2.)
    parser.add_argument('--depth-mode',choices=['scene','analytic'],default='scene',
                        help='Scene optical Z with full occlusion (default), or historical v4 ball-only ray distance')
    parser.add_argument('--camera-profile',type=Path,
                        help='v5 camera calibration profile; must match a scene-trained export when present')
    parser.add_argument('--serve-mode',choices=['recovery','fixed'],default='recovery')
    parser.add_argument('--depth-output',type=Path,help='Save actual policy depth as MP4, PNG and raw NPZ (10 fps)')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/agilekickball_v4/sim2sim_20261014/run.json')
    raise SystemExit(run(parser.parse_args()))
