"""Noisy scene-depth football on the wall11 physical/control framework."""
from types import SimpleNamespace
import torch
from isaaclab.envs import ManagerBasedRLEnv
from isaaclab.utils.math import quat_apply_inverse, quat_inv, quat_mul, yaw_quat, matrix_from_quat
from perceptual_ball.amp_features import relative_base_height, pack_amp_frame
from perceptual_ball.kickball_v11 import KickballV11State, KickMotionLibrary, MOTION_DIR, REVISION
from . import carrybox as base
from . import carrybox_wall10 as control
from .carrybox_wall11 import depth_image
from .carrybox_walled import reference_ground_correction
from .amp import END_EFFECTOR_BODY_NAMES


def setup(env, env_ids):
    env._kickball = KickballV11State(env)


def curriculum(env, env_ids):
    env._kickball._sync_course()
    return env._kickball.serve_speed_range[1]


def reset_scene(env, env_ids):
    robot = env.scene['robot']
    root = robot.data.default_root_state[env_ids].clone()
    root[:, :3] += env.scene.env_origins[env_ids]
    root[:, 7:] = 0.
    joint = robot.data.default_joint_pos[env_ids].clone()
    # The COM writer does not refresh Isaac Lab's cached root-link velocity.
    # Reset both frames explicitly so critic/labels see this standing state.
    robot.write_root_link_state_to_sim(root, env_ids=env_ids)
    robot.write_joint_state_to_sim(joint, torch.zeros_like(joint), env_ids=env_ids)
    env.sim.forward()
    if not hasattr(env, '_walled'):
        env._walled = SimpleNamespace()  # Cache only the shared foot-hull helper.
    correction = reference_ground_correction(env, env_ids)
    if not torch.isfinite(correction).all():
        raise FloatingPointError('Nonfinite kickballv11 foot clearance')
    root[:, 2] += correction
    robot.write_root_pose_to_sim(root[:, :7], env_ids=env_ids)
    env.sim.forward()
    env._kickball.reset(env_ids)
    if hasattr(env, '_wall10_noisy_step'):
        env._wall10_noisy_step[env_ids] = -1
    if hasattr(env, '_wall11_depth'):
        env._wall11_depth.reset(env_ids)


def ball_target(env):
    r, b = env.scene['robot'].data, env.scene['ball'].data
    q = r.root_link_quat_w
    xyz = quat_apply_inverse(q, b.root_pos_w - r.root_link_pos_w)
    velocity = quat_apply_inverse(q, b.root_lin_vel_w - r.root_link_lin_vel_w)
    return torch.cat((xyz, velocity), -1).detach()


def critic_state(env):
    r = env.scene['robot'].data
    q = r.root_link_quat_w
    ends = quat_apply_inverse(q[:, None].expand(-1, 5, -1),
        r.body_link_pos_w[:, control.body_ids(env)] - r.root_link_pos_w[:, None]).flatten(1)
    source = r.root_link_pos_w.clone()
    normal = torch.zeros_like(source)
    width = torch.zeros(env.num_envs, 1, device=env.device)
    if hasattr(env, '_kickball'):
        source[:, :2] = env._kickball.source_xy
        source[:, 2] = env.scene.env_origins[:, 2] + .11
        normal[:, :2] = env._kickball.return_normal
        width[:, 0] = env._kickball.round_half_width
    return torch.cat((base.proprioception(env), ends, quat_apply_inverse(q, r.root_link_lin_vel_w) * 2.,
        ball_target(env), quat_apply_inverse(q, source - r.root_link_pos_w),
        quat_apply_inverse(q, normal), width), -1).detach()


def amp_frame(env):
    robot = env.scene['robot']
    if not hasattr(env, '_kick_amp_bodies'):
        env._kick_amp_bodies = robot.find_bodies(END_EFFECTOR_BODY_NAMES, preserve_order=True)[0]
        if len(env._kick_amp_bodies) != 5:
            raise ValueError('Kick reference needs wrist_roll/ankle_pitch/head_link end points')
    r = robot.data
    ends = r.body_link_pos_w[:, env._kick_amp_bodies]
    q = r.root_quat_w
    local = quat_apply_inverse(q[:, None].expand(-1, 5, -1), ends - r.root_pos_w[:, None]).flatten(1)
    rot = matrix_from_quat(quat_mul(quat_inv(yaw_quat(q)), q))[..., :2].reshape(env.num_envs, 6)
    return pack_amp_frame(relative_base_height(r.root_pos_w, ends), r.joint_pos, local,
                          r.root_lin_vel_b, r.root_ang_vel_b, rot)


class KickballV11Env(base.CarryBoxEnv):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._wall10_previous_velocity = torch.zeros_like(self.scene['robot'].data.joint_vel)
        self._wall10_torso = self.scene['robot'].find_bodies('torso_link')[0]
        self._wall10_zero_force = torch.zeros(self.num_envs, 1, 3, device=self.device)
        self._wall10_force = self._wall10_zero_force
        self._wall10_force_pending = False

    def step(self, action):
        self._wall10_previous_velocity.copy_(self.scene['robot'].data.joint_vel)
        self._wall10_previous_velocity[self.episode_length_buf == 0] = 0.
        self._wall10_force_pending = self.common_step_counter > 0 and self.common_step_counter % 8 == 0
        self._wall10_force = (torch.empty_like(self._wall10_zero_force).uniform_(-50., 50.)
                             if self._wall10_force_pending else self._wall10_zero_force)
        result = super().step(action)
        result[-1].setdefault('log', {}).update(self._kickball.metrics())
        return result

    def terminal_frame(self, group):
        return {'proprio': control.proprioception, 'perception': depth_image, 'amp': amp_frame}[group](self)

    def _reset_idx(self, env_ids):
        terminal = None
        if getattr(self, '_carrybox_in_step', False):
            terminal = dict(critic_state=critic_state(self)[env_ids].clone(),
                            ball_target=ball_target(self)[env_ids].clone())
            for group, length in (('proprio', 6), ('perception', 4), ('amp', 10)):
                frame = self.terminal_frame(group)[env_ids]
                history = self.observation_manager.compute_group(group)[env_ids].reshape(
                    len(env_ids), length, *frame.shape[1:])
                current = torch.cat((history[:, 1:], frame[:, None]), 1)
                terminal[group] = current if group == 'perception' else current.flatten(1)
        ManagerBasedRLEnv._reset_idx(self, env_ids)
        self.sim.forward()
        if terminal is not None:
            self._carrybox_terminal = dict(env_ids=env_ids.clone(), obs=terminal)

    @property
    def depth_contract(self):
        camera = self.scene['depth_camera'].cfg
        return dict(schema=1, output='optical_z_metres', units='metres', normalization='none',
            clip_range_m=[.1, 3.], invalid_depth_m=3., input_range=[.1, 3.], missing_value=3.,
            shape=[4, 27, 48], history_order='oldest_to_newest', geometry='robot_ground_ball',
            noise=dict(self.cfg.depth_noise), capture='once_per_step_partial_reset_or_serve_invalidated',
            camera=dict(parent='torso_link', position=list(camera.offset.pos),
                        quaternion_wxyz=list(camera.offset.rot), vertical_fov_deg=58.))

    def checkpoint_contract(self):
        return dict(variant='kickballv11', revision=REVISION, parent='wall11_control_learning',
            task='v4_continuous_return_to_sender', curriculum=self._kickball.course_config,
            actor='proprio93x6_depth4x27x48', critic='proprio93_ends15_lin3_ball6_source3_normal3_width1',
            auxiliary='root_xyz_and_relative_inertial_velocity_all_frames_no_actor_feedback',
            depth=self.depth_contract, proprio_noise=self.cfg.proprio_noise, reset='standing_zero_velocity_clearance5mm',
            actor_privileged=False, obstacles=False, amp=KickMotionLibrary(MOTION_DIR).metadata,
            control='wall11_explicit_PD_strength_bias_delay0to20ms_action100',
            disturbance='local_torso_xyz50N_every8_policy_steps',
            randomization=dict(link_mass=[.8,1.2], torso_com=[-.1,.1], friction=[.1,1.5],
                restitution=[0.,1.], kp_kd_motor=[.9,1.1], torque_bias_fraction=[-.05,.05]),
            rewards={k:v.weight for k,v in vars(self.cfg.rewards).items() if hasattr(v,'weight')},
            physics_dt=self.sim.get_physics_dt(), decimation=self.cfg.decimation,
            episode_s=self.cfg.episode_length_s, ball_radius=.11, ball_mass=.43)
