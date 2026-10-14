"""Find and lift a physical box. Ground truth is restricted to training labels/task scoring."""
import math
import torch
from isaaclab.envs import ManagerBasedRLEnv
from isaaclab.utils.math import quat_apply_inverse, quat_mul, quat_conjugate, matrix_from_quat, quat_from_euler_xyz
from .carrybox_state import LiftHoldState
from perceptual_ball.carrybox_amp import AMP_WINDOW, joint_mapping, pack_frame

BOX_SIZE = (.30, .30, .25)


def amp_frame(env):
    """Same 64 sensor-observable features as the expert, in source named joint order."""
    robot = env.scene['robot']
    if not hasattr(env, '_carrybox_amp_joint_ids'):
        env._carrybox_amp_joint_ids = joint_mapping(robot.joint_names)
    ids = env._carrybox_amp_joint_ids
    return pack_frame(robot.data.joint_pos[:, ids], robot.data.joint_vel[:, ids],
                      robot.data.projected_gravity_b, robot.data.root_ang_vel_b)


def proprioception(env):
    robot = env.scene['robot'].data
    return torch.cat((robot.root_ang_vel_b * .25, robot.projected_gravity_b,
                      robot.joint_pos - robot.default_joint_pos,
                      (robot.joint_vel - robot.default_joint_vel) * .05,
                      env.action_manager.action), -1)


def depth_image(env):
    """Rendered optical-axis depth, normalized to [0,1]; no segmentation or state ROI."""
    depth = env.scene['depth_camera'].data.output['distance_to_image_plane'][..., 0]
    return torch.nan_to_num(depth, nan=3., posinf=3., neginf=3.).clamp(.1, 3.) / 3.


def box_pose_target(env):
    # Access updates the camera at the same control-step render as depth_image. The camera
    # must have update_latest_camera_pose=True; otherwise IsaacLab returns its initial pose.
    camera = env.scene['depth_camera'].data
    box = env.scene['box'].data
    xyz = quat_apply_inverse(camera.quat_w_ros, box.root_pos_w - camera.pos_w)
    rotation = matrix_from_quat(quat_mul(quat_conjugate(camera.quat_w_ros), box.root_quat_w))
    return torch.cat((xyz, rotation[..., :2].transpose(-1, -2).flatten(-2)), -1).detach()


def reset_box(env, env_ids):
    if not hasattr(env, '_carrybox_hold'):
        env._carrybox_hold = LiftHoldState(env.num_envs, env.device, math.ceil(.5 / env.step_dt))
    box = env.scene['box']
    state = box.data.default_root_state[env_ids].clone()
    count = len(env_ids)
    state[:, :3] = env.scene.env_origins[env_ids]
    state[:, 0] += torch.empty(count, device=env.device).uniform_(.65, 1.25)
    state[:, 1] += torch.empty(count, device=env.device).uniform_(-.25, .25)
    state[:, 2] += BOX_SIZE[2] / 2 + .005
    zeros = torch.zeros(count, device=env.device)
    yaw = torch.empty(count, device=env.device).uniform_(-math.pi, math.pi)
    state[:, 3:7] = quat_from_euler_xyz(zeros, zeros, yaw)
    state[:, 7:] = 0.
    box.write_root_state_to_sim(state, env_ids=env_ids)
    env._carrybox_hold.reset(env_ids)


def hand_contacts(env):
    # Each sensor is attached to one actual rubber-hand rigid body, filtered to Box.
    return torch.stack([env.scene[f'{side}_box_contact'].data.force_matrix_w.flatten(1, -2).norm(dim=-1).amax(-1) > 1.
                        for side in ('left', 'right')], -1)


def lift_geometry(env):
    box = env.scene['box'].data
    rot = matrix_from_quat(box.root_quat_w)
    half = torch.tensor(BOX_SIZE, device=env.device) / 2
    bottom = box.root_pos_w[:, 2] - env.scene.env_origins[:, 2] - (rot[:, 2].abs() * half).sum(-1)
    return bottom, rot[:, 2, 2], box.root_lin_vel_w.norm(dim=-1)


def lift_success(env):
    if not hasattr(env, '_carrybox_hold'):
        return torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
    bottom, upright, speed = lift_geometry(env)
    return env._carrybox_hold.update(env.common_step_counter, bottom, hand_contacts(env), upright, speed)


def approach_box(env):
    robot, box = env.scene['robot'].data, env.scene['box'].data
    delta = box.root_pos_w - robot.root_pos_w
    local = quat_apply_inverse(robot.root_quat_w, delta)
    distance = delta[:, :2].norm(dim=-1)
    facing = torch.exp(-torch.atan2(local[:, 1], local[:, 0]).square())
    return torch.exp(-2. * (distance - .45).clamp_min(0)) * facing


def reach_box(env):
    robot, box = env.scene['robot'], env.scene['box'].data
    if not hasattr(env, '_carrybox_hand_ids'):
        env._carrybox_hand_ids = robot.find_bodies(['left_rubber_hand', 'right_rubber_hand'], preserve_order=True)[0]
    hands = robot.data.body_pos_w[:, env._carrybox_hand_ids]
    q = box.root_quat_w[:, None, :].expand(-1, 2, -1)
    local = quat_apply_inverse(q.reshape(-1, 4), (hands - box.root_pos_w[:, None]).reshape(-1, 3)).reshape(-1, 2, 3)
    half = torch.tensor(BOX_SIZE, device=env.device) / 2
    surface_distance = (local - local.clamp(-half, half)).norm(dim=-1)
    # Both hands close to distinct surfaces; avoids maximizing reward with only one hand.
    separation = (hands[:, 0] - hands[:, 1]).norm(dim=-1).clamp(max=.25) / .25
    return torch.exp(-8 * surface_distance.sum(-1)) * separation


def lift_box(env):
    bottom, upright, _ = lift_geometry(env)
    return (bottom / .25).clamp(0, 1) * (upright > .8) * hand_contacts(env).all(-1)


def invalid_state(env):
    for value in (env.scene['robot'].data.root_state_w, env.scene['robot'].data.joint_pos,
                  env.scene['robot'].data.joint_vel, env.scene['box'].data.root_state_w,
                  env.action_manager.action):
        if not torch.isfinite(value).all():
            raise FloatingPointError('Non-finite CarryBox state/action')
    return torch.zeros(env.num_envs, device=env.device, dtype=torch.bool)


class CarryBoxEnv(ManagerBasedRLEnv):
    """Preserve terminal visual histories for correct timeout bootstrapping."""
    def step(self, action):
        if not torch.isfinite(action).all():
            raise FloatingPointError('Non-finite CarryBox action')
        self._carrybox_terminal = None
        self._carrybox_in_step = True
        try:
            obs, reward, terminated, truncated, extras = super().step(action)
        finally:
            self._carrybox_in_step = False
        if self._carrybox_terminal is None:
            extras.pop('terminal_observations', None)
        else:
            extras['terminal_observations'] = self._carrybox_terminal
        return obs, reward, terminated, truncated, extras

    def terminal_frame(self, group):
        return {'proprio': proprioception, 'perception': depth_image, 'amp': amp_frame}[group](self)

    def _reset_idx(self, env_ids):
        if getattr(self, '_carrybox_in_step', False):
            terminal = {}
            for group in ('proprio', 'perception', 'amp'):
                # One term per group: shift a copy, never append twice for surviving envs.
                frame = self.terminal_frame(group)[env_ids]
                history = self.observation_manager.compute_group(group)[env_ids]
                length = AMP_WINDOW if group == 'amp' else 4
                history = history.reshape(len(env_ids), length, *frame.shape[1:])
                current = torch.cat((history[:, 1:], frame[:, None]), 1)
                terminal[group] = current if group == 'perception' else current.flatten(1)
            self._carrybox_terminal = dict(env_ids=env_ids.clone(), obs=terminal)
        super()._reset_idx(env_ids)
