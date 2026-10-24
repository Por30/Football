"""PhysHSI G1 control and reset, with FindBox depth and stationary lift completion."""
import math
from types import SimpleNamespace
import torch
from isaaclab.actuators import IdealPDActuator
from isaaclab.envs import ManagerBasedRLEnv
from isaaclab.envs.mdp import JointPositionAction
from isaaclab.utils.math import (quat_apply, quat_apply_inverse, quat_mul, quat_conjugate,
                                matrix_from_quat, quat_from_euler_xyz, wrap_to_pi)
from perceptual_ball.carrybox_physhsi import PhysicalActionDelay, sample_hybrid
from perceptual_ball.carrybox_amp import joint_mapping
from perceptual_ball.carrybox_wall5 import AMP_BODY_NAMES
from perceptual_ball.carrybox_wall10 import pack_frame, task_rewards, lift_hold_mask
from perceptual_ball.carrybox_warp_camera import WarpDepthCamera
from . import carrybox as base
from . import carrybox_walled as wall
from .carrybox_physhsi import initialize_reference


class Wall10Actuator(IdealPDActuator):
    """Source explicit PD, motor strength and effort offset, followed by effort clipping."""
    def __init__(self, *args, **kwargs):
        # Explicit actuator defaults otherwise replace the imported URDF effort
        # limit by 1e9; retain the actual motor limits for both clipping paths.
        source_limit = kwargs['effort_limit'].clone()
        super().__init__(*args, **kwargs)
        self.effort_limit.copy_(source_limit)
        self.effort_limit_sim.copy_(source_limit)
        self.kp_factor = torch.ones_like(self.stiffness)
        self.kd_factor = torch.ones_like(self.damping)
        self.motor_strength = torch.ones_like(self.stiffness)
        self.effort_offset = torch.zeros_like(self.stiffness)

    def reset(self, env_ids):
        for tensor in (self.kp_factor, self.kd_factor, self.motor_strength):
            tensor[env_ids] = torch.empty_like(tensor[env_ids]).uniform_(.9, 1.1)
        self.effort_offset[env_ids] = torch.empty_like(self.effort_offset[env_ids]).uniform_(-.05, .05) * self.effort_limit[env_ids]

    def compute(self, control_action, joint_pos, joint_vel):
        torque = (self.stiffness * self.kp_factor * (control_action.joint_positions - joint_pos)
                  - self.damping * self.kd_factor * joint_vel)
        self.computed_effort = torque * self.motor_strength + self.effort_offset
        if not torch.isfinite(self.computed_effort).all():
            raise FloatingPointError('Nonfinite wall10 explicit PD effort')
        self.applied_effort = self._clip_effort(self.computed_effort)
        control_action.joint_efforts = self.applied_effort
        control_action.joint_positions = control_action.joint_velocities = None
        return control_action


class Wall10JointPositionAction(JointPositionAction):
    def __init__(self, cfg, env):
        super().__init__(cfg, env)
        self.delay = PhysicalActionDelay(self._asset.data.joint_pos[:, self._joint_ids])

    def apply_actions(self):
        self._asset.set_joint_position_target(self.delay.advance(self._processed_actions), joint_ids=self._joint_ids)
        force = self._env._wall10_force
        self._asset.set_external_force_and_torque(force, torch.zeros_like(force), body_ids=self._env._wall10_torso)
        # Isaac Gym external force applies to the next simulation step only.
        self._env._wall10_force = torch.zeros_like(force)

    def reset(self, env_ids=None):
        super().reset(env_ids)
        ids = self.delay.rows if env_ids is None else env_ids
        pose = self._asset.data.joint_pos[ids][:, self._joint_ids]
        self.delay.reset(ids, pose)
        self._processed_actions[ids] = pose
        self._asset.set_joint_position_target(pose, joint_ids=self._joint_ids, env_ids=ids)


def spawn_box(prim_path, cfg, **kwargs):
    """Per-environment source size grid and density; do not clone one sampled box."""
    import isaaclab.sim as sim
    from pxr import Sdf, Gf
    parent, name = prim_path.rsplit('/', 1)
    roots = sim.find_matching_prim_paths(parent)
    first = None
    for root in roots:
        scale = torch.tensor([torch.randint(7, 14, ()).item(), torch.randint(7, 14, ()).item(),
                              torch.randint(6, 15, ()).item()]) / 10
        size = tuple((scale * torch.tensor(base.BOX_SIZE)).tolist())
        density = float(torch.empty(()).uniform_(10., 100.))
        config = cfg.copy()
        config.func = sim.spawn_cuboid
        config.size = size
        config.mass_props.mass = math.prod(size) * density
        prim = sim.spawn_cuboid(root + '/' + name, config, **kwargs)
        prim.CreateAttribute('wall10:size', Sdf.ValueTypeNames.Float3).Set(Gf.Vec3f(*size))
        first = prim if first is None else first
    return first


class Wall10DepthCamera(WarpDepthCamera):
    """Shared robot/obstacle BVHs plus exact per-environment oriented box geometry."""
    def _initialize_impl(self):
        super()._initialize_impl()
        self._box_view = self._physics.create_rigid_body_view('/World/envs/env_*/Box')
        paths = [f'/World/envs/env_{i}/Box' for i in range(self._num_envs)]
        if self._box_view.prim_paths != paths:
            raise RuntimeError('Wall10 box/environment ordering differs')
        self.box_sizes = torch.tensor([list(self.stage.GetPrimAtPath(p).GetAttribute('wall10:size').Get())
                                       for p in paths], device=self.device)

    def _update_buffers_impl(self, env_ids):
        super()._update_buffers_impl(env_ids)
        pose = self._box_view.get_transforms()[env_ids]
        q = pose[:, [6, 3, 4, 5]]
        direction = quat_apply(self._data.quat_w_world[env_ids, None].expand(-1, len(self._rays), -1),
                               self._rays[None].expand(len(env_ids), -1, -1))
        origin = self._data.pos_w[env_ids, None] + direction * (self.cfg.near / self._rays[:, 0])[None, :, None]
        q = q[:, None].expand(-1, len(self._rays), -1)
        local_origin = quat_apply_inverse(q, origin - pose[:, None, :3])
        local_direction = quat_apply_inverse(q, direction)
        half = self.box_sizes[env_ids, None] / 2
        parallel = local_direction.abs() < 1.e-8
        safe = torch.where(parallel, torch.ones_like(local_direction), local_direction)
        a, b = (-half - local_origin) / safe, (half - local_origin) / safe
        low = torch.where(parallel, -torch.inf, torch.minimum(a, b)).amax(-1)
        high = torch.where(parallel, torch.inf, torch.maximum(a, b)).amin(-1)
        hit = (high >= low.clamp_min(0)) & ~(parallel & (local_origin.abs() > half)).any(-1)
        distance = torch.where(low >= 0, low, high)
        depth = torch.where(hit, self.cfg.near + distance * self._rays[:, 0], self.cfg.far)
        self._depth[env_ids] = torch.minimum(self._depth[env_ids], depth.clamp(self.cfg.near, self.cfg.far))


def state(env):
    if not hasattr(env, '_walled'):
        n, device = env.num_envs, env.device
        env._walled = SimpleNamespace(library=None, references=None,
            skills=torch.zeros(n, dtype=torch.long, device=device),
            default_reset=torch.ones(n, dtype=torch.bool, device=device),
            hold_steps=torch.zeros(n, dtype=torch.long, device=device),
            achieved=torch.zeros(n, dtype=torch.bool, device=device),
            from_ground=torch.zeros(n, dtype=torch.bool, device=device),
            anchor=torch.zeros(n, 2, device=device), reward_step=None,
            reset_counts=torch.zeros(4, dtype=torch.long, device=device),
            episode_counts=torch.zeros(4, dtype=torch.long, device=device),
            success_counts=torch.zeros(4, dtype=torch.long, device=device),
            ground_episodes=torch.zeros((), dtype=torch.long, device=device),
            ground_successes=torch.zeros((), dtype=torch.long, device=device))
    return env._walled


def robot_material(env, env_ids):
    view = env.scene['robot'].root_physx_view
    values = view.get_material_properties()
    ids = torch.arange(env.num_envs) if env_ids is None else env_ids.cpu()
    friction = torch.empty(len(ids), 1).uniform_(.1, 1.5)
    restitution = torch.empty(len(ids), 1).uniform_(0., 1.)
    values[ids, :, 0] = friction
    values[ids, :, 1] = friction
    values[ids, :, 2] = restitution
    view.set_material_properties(values, ids)


def reset_scene(env, env_ids):
    s, box = state(env), env.scene['box']
    n = len(env_ids)
    skills, defaults = sample_hybrid(n, env.device)
    s.skills[env_ids], s.default_reset[env_ids] = skills, defaults
    s.reset_counts += torch.bincount(torch.where(defaults, 0, skills + 1), minlength=4)
    reference, support = initialize_reference(env, env_ids)
    robot = env.scene['robot'].data
    size = env.scene['depth_camera'].box_sizes[env_ids]
    ground = env.scene.env_origins[env_ids, 2]
    pose = box.data.default_root_state[env_ids].clone()
    angle = torch.empty(n, device=env.device).uniform_(-math.pi / 4, math.pi / 4)
    radius = torch.empty(n, device=env.device).uniform_(.7, 2.)
    yaw = wall.heading(robot.root_link_quat_w[env_ids])
    bearing = angle + yaw
    pose[:, :2] = robot.root_link_pos_w[env_ids, :2] + radius[:, None] * torch.stack((bearing.cos(), bearing.sin()), -1)
    pose[:, 2] = ground + size[:, 2] / 2 + .005
    reference_rows = skills != 0
    pose[reference_rows, :3] = reference[reference_rows]
    pose[:, 2] = torch.maximum(pose[:, 2], ground + size[:, 2] / 2 + .005)
    # Source RSI box orientation follows the paired root yaw, with 180deg symmetry.
    box_yaw = torch.empty(n, device=env.device).uniform_(-math.pi, math.pi)
    box_yaw[reference_rows] = yaw[reference_rows] + torch.randint(2, (int(reference_rows.sum()),), device=env.device) * math.pi
    zeros = torch.zeros(n, device=env.device)
    pose[:, 3:7] = quat_from_euler_xyz(zeros, zeros, box_yaw)
    pose[:, 7:] = 0
    box.write_root_state_to_sim(pose, env_ids=env_ids)
    platform = pose[:, :7].clone()
    active = s.support_active[env_ids]
    platform[:, 2] = torch.where(active, pose[:, 2] - size[:, 2] / 2 - .005 - .01, ground - 5.)
    platform[:, 3:7] = platform.new_tensor([1., 0., 0., 0.])
    wall.write_obstacle_pose(env, 'platform', platform, env_ids)
    # FindBox context wall stays behind the box search area; no destination platform.
    obstacle = platform.clone()
    obstacle[:, :2] = env.scene.env_origins[env_ids, :2]
    obstacle[:, 0] -= 3.5
    obstacle[:, 2] = ground + 1.5
    wall.write_obstacle_pose(env, 'wall', obstacle, env_ids)
    s.anchor[env_ids] = pose[:, :2]
    s.from_ground[env_ids] = (pose[:, 2] - ground - size[:, 2] / 2) < .03
    s.hold_steps[env_ids] = 0
    s.achieved[env_ids] = False
    s.reward_step = None
    if hasattr(env, '_wall10_noisy_step'):
        env._wall10_noisy_step[env_ids] = -1


def proprioception(env):
    raw = base.proprioception(env)
    if not env.cfg.proprio_noise:
        return raw.clamp(-100, 100)
    if not hasattr(env, '_wall10_noisy'):
        env._wall10_noisy = raw.clone()
        env._wall10_noisy_step = torch.full((env.num_envs,), -1, device=env.device, dtype=torch.long)
        env._wall10_noise_scale = raw.new_tensor([.075] * 3 + [.05] * 3 + [.02] * 29 + [.1] * 29 + [0.] * 29)
    fresh = env._wall10_noisy_step != env.common_step_counter
    env._wall10_noisy[fresh] = (raw[fresh] + (2 * torch.rand_like(raw[fresh]) - 1) * env._wall10_noise_scale).clamp(-100, 100)
    env._wall10_noisy_step[fresh] = env.common_step_counter
    return env._wall10_noisy


def body_ids(env):
    if not hasattr(env, '_wall10_body_ids'):
        env._wall10_body_ids = env.scene['robot'].find_bodies(list(AMP_BODY_NAMES), preserve_order=True)[0]
        env._wall10_joint_ids = joint_mapping(env.scene['robot'].joint_names)
    return env._wall10_body_ids


def critic_state(env):
    robot, box = env.scene['robot'].data, env.scene['box'].data
    q = robot.root_link_quat_w
    ends = quat_apply_inverse(q[:, None].expand(-1, 5, -1),
                             robot.body_link_pos_w[:, body_ids(env)] - robot.root_link_pos_w[:, None]).flatten(1)
    xyz = quat_apply_inverse(q, box.root_pos_w - robot.root_link_pos_w)
    rot = matrix_from_quat(quat_mul(quat_conjugate(q), box.root_quat_w))
    rot6 = torch.cat((rot[..., 0], rot[..., 2]), -1)
    return torch.cat((base.proprioception(env), ends,
        quat_apply_inverse(q, robot.root_link_lin_vel_w) * 2., xyz, rot6,
        env.scene['depth_camera'].box_sizes), -1).detach().clamp(-100, 100)


def amp_frame(env):
    robot = env.scene['robot'].data
    ids = body_ids(env)
    return pack_frame(robot.joint_pos[:, env._wall10_joint_ids], robot.root_link_quat_w,
        robot.body_link_pos_w[:, ids] - robot.root_link_pos_w[:, None],
        robot.root_link_lin_vel_w, robot.root_link_ang_vel_b,
        env.scene['box'].data.root_pos_w - robot.root_link_pos_w)


def depth_image(env):
    return env.scene['depth_camera'].data.output['distance_to_image_plane'][..., 0].nan_to_num(nan=3., posinf=3., neginf=3.).clamp(.1, 3.)


def reward_terms(env):
    s = state(env)
    if s.reward_step == env.common_step_counter:
        return s.rewards
    r, b = env.scene['robot'].data, env.scene['box'].data
    ids = body_ids(env)
    delta = b.root_pos_w - r.root_link_pos_w
    distance = delta[:, :2].norm(dim=-1)
    toward = (delta[:, :2] / distance.clamp_min(1.e-6)[:, None] * r.root_link_lin_vel_w[:, :2]).sum(-1)
    bearing = wrap_to_pi(torch.atan2(delta[:, 1], delta[:, 0]) - wall.heading(r.root_link_quat_w))
    hands = r.body_link_pos_w[:, ids[:2]].mean(1)
    error = (hands - b.root_pos_w).square().sum(-1)
    ground = env.scene.env_origins[:, 2]
    rotation = matrix_from_quat(b.root_quat_w)
    height = b.root_pos_w[:, 2] - ground
    clearance = height - (rotation[:, 2].abs() * env.scene['depth_camera'].box_sizes / 2).sum(-1)
    contacts = base.hand_contacts(env)
    head_height = r.body_link_pos_w[:, ids[4], 2] - ground
    speed = r.root_link_lin_vel_w[:, :2].norm(dim=-1)
    angular = r.root_link_ang_vel_b.norm(dim=-1)
    box_speed = b.root_lin_vel_w.norm(dim=-1)
    drift = (b.root_pos_w[:, :2] - s.anchor).norm(dim=-1)
    held = contacts.all(-1) & (clearance > .10) & (rotation[:, 2, 2] > .8)
    valid = lift_hold_mask(clearance, contacts, rotation[:, 2, 2], -r.projected_gravity_b[:, 2],
                          head_height, speed, r.root_link_ang_vel_b[:, 2].abs(), box_speed, drift, height)
    s.hold_steps = torch.where(valid, s.hold_steps + 1, 0)
    s.achieved |= s.hold_steps >= math.ceil(env.cfg.hold_duration_s / env.step_dt)
    s.rewards = task_rewards(distance, toward, bearing, error, height, held, head_height, speed, angular, box_speed, drift)
    s.reward_step = env.common_step_counter
    return s.rewards


def task_reward(env, name):
    return reward_terms(env)[name]


def normalized_torque(env):
    r = env.scene['robot'].data
    return (r.applied_torque / r.default_joint_stiffness.clamp_min(1.e-6)).square().sum(-1)


def torque_limits(env):
    r = env.scene['robot'].data
    return (r.computed_torque.abs() - .95 * r.joint_effort_limits).clamp_min(0).sum(-1)


def velocity_limits(env):
    r = env.scene['robot'].data
    return (r.joint_vel.abs() - .8 * r.joint_vel_limits).clamp_min(0).sum(-1)


def policy_acceleration(env):
    return ((env.scene['robot'].data.joint_vel - env._wall10_previous_velocity) / env.step_dt).square().sum(-1)


class Wall10CarryBoxEnv(base.CarryBoxEnv):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._wall10_previous_velocity = torch.zeros_like(self.scene['robot'].data.joint_vel)
        self._wall10_torso = self.scene['robot'].find_bodies('torso_link')[0]
        self._wall10_force = torch.zeros(self.num_envs, 1, 3, device=self.device)

    def step(self, action):
        if not hasattr(self, '_wall10_previous_velocity'):
            self._wall10_previous_velocity = torch.zeros_like(self.scene['robot'].data.joint_vel)
        self._wall10_previous_velocity.copy_(self.scene['robot'].data.joint_vel)
        self._wall10_previous_velocity[self.episode_length_buf == 0] = 0.
        # Source applies a local torso pulse every 8 policy steps, not every 8 seconds.
        force = torch.zeros(self.num_envs, 1, 3, device=self.device)
        if self.common_step_counter > 0 and self.common_step_counter % 8 == 0:
            force.uniform_(-50., 50.)
        self._wall10_force = force
        result = super().step(action)
        s = state(self)
        log = result[-1].setdefault('log', {})
        for i, label in enumerate(('default', 'loco_rsi', 'pickup_rsi', 'hold_rsi')):
            log[f'Wall10/{label}_episodes'] = s.episode_counts[i].float()
            log[f'Wall10/{label}_success_fraction'] = s.success_counts[i] / s.episode_counts[i].clamp_min(1)
        log['Wall10/ground_start_episodes'] = s.ground_episodes.float()
        log['Wall10/ground_start_success_fraction'] = s.ground_successes / s.ground_episodes.clamp_min(1)
        log['Wall10/hold_fraction'] = (s.hold_steps > 0).float().mean()
        return result

    def terminal_frame(self, group):
        return {'proprio': proprioception, 'perception': depth_image, 'amp': amp_frame}[group](self)

    def _reset_idx(self, env_ids):
        s = state(self)
        terminal = None
        if getattr(self, '_carrybox_in_step', False):
            terminal = {'critic_state': critic_state(self)[env_ids].clone()}
            for group in ('proprio', 'perception', 'amp'):
                frame = self.terminal_frame(group)[env_ids]
                length = getattr(self.cfg.observations, group).__dict__
                term = next(v for v in length.values() if hasattr(v, 'history_length'))
                history = self.observation_manager.compute_group(group)[env_ids].reshape(len(env_ids), term.history_length, *frame.shape[1:])
                current = torch.cat((history[:, 1:], frame[:, None]), 1)
                terminal[group] = current if group == 'perception' else current.flatten(1)
            source = torch.where(s.default_reset[env_ids], 0, s.skills[env_ids] + 1)
            s.episode_counts += torch.bincount(source, minlength=4)
            s.success_counts += torch.bincount(source[s.achieved[env_ids]], minlength=4)
            s.ground_episodes += s.from_ground[env_ids].sum()
            s.ground_successes += (s.from_ground[env_ids] & s.achieved[env_ids]).sum()
        # Generic manager reset supports the 6-frame proprio / 4-frame depth split.
        ManagerBasedRLEnv._reset_idx(self, env_ids)
        self.sim.forward()
        if terminal is not None:
            self._carrybox_terminal = dict(env_ids=env_ids.clone(), obs=terminal)

    @property
    def depth_contract(self):
        return dict(schema=1, output='optical_z_metres', units='metres', normalization='none',
                    clip_range_m=[.1, 3.], invalid_depth_m=3., input_range=[.1, 3.], missing_value=3.,
                    shape=[4, 27, 48], history_order='oldest_to_newest', geometry='robot_ground_wall_support_variable_box')

    def checkpoint_contract(self):
        import hashlib
        from pathlib import Path
        return dict(variant='walled10', migration_revision=1, source='PhysHSI_G1_carrybox',
            task='approach_lift_stationary_hold_no_goal_no_putdown', hold_seconds=self.cfg.hold_duration_s,
            actor='proprio93x6_depth4x27x48', critic='proprio93_ends15_lin3_box12',
            depth=self.depth_contract, actor_proprio_noise=self.cfg.proprio_noise,
            control='explicit_PD_motor_strength_effort_offset_delay0to20ms_action100_no_target_clip',
            reset='bernoulli80_RSI_conditional_2over3_1over6_1over6_ground_correction5mm',
            reset_history='repeat_first_current_frame',
            observations='no_goal_no_phase_no_success_flag_actor_no_privileged',
            box_size_scale=[[.7,1.3],[.7,1.3],[.6,1.4]], box_density=[10.,100.],
            rigid_body_randomization=dict(link_mass=[.8,1.2], recompute_inertia=True,
                torso_com_xyz=[-.1,.1], robot_friction=[.1,1.5], robot_restitution=[0.,1.],
                kp_kd_motor_strength=[.9,1.1], effort_offset_limit_fraction=[-.05,.05]),
            support_size=[.4,.4,.02], ground_friction=.9,
            success_thresholds=dict(box_bottom_min=.10, box_center_min=.70, bilateral_force_min=1.,
                box_upright_min=.8, robot_upright_min=.95, head_min=1.05,
                root_xy_speed_max=.15, root_yaw_speed_max=.3, box_speed_max=.15, box_xy_drift_max=.35),
            box_regular_spawn='front_0.7to2m_yaw45deg_ground',
            rewards={k:v.weight for k,v in vars(self.cfg.rewards).items() if hasattr(v,'weight')},
            torque_penalty='applied_div_nominal_kp_squared',
            disturbance='local_torso_uniform_xyz50N_every8_policy_steps',
            physics_dt=self.sim.get_physics_dt(), decimation=self.cfg.decimation, episode_s=self.cfg.episode_length_s,
            dataset_sha256=hashlib.sha256((Path(self.cfg.reference_motion_dataset)/'amp_manifest.json').read_bytes()).hexdigest())
