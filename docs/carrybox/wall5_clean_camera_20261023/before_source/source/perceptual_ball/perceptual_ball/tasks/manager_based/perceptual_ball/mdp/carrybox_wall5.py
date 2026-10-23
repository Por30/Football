"""Wall5 AMP observation contract and versioned full-body collision geometry."""
import hashlib
import math
import torch
from isaaclab.utils.math import (euler_xyz_from_quat, wrap_to_pi, quat_apply_inverse,
                               quat_mul, quat_conjugate, matrix_from_quat)
from perceptual_ball.carrybox_amp import joint_mapping
from pathlib import Path
from perceptual_ball.carrybox_wall5 import (pack_task_frame, AMP_BODY_NAMES, WALL5_FEATURE_SCHEMA,
    GROUND_RESET_PROFILE, grasp_components, AMP_DATASET_PATH)
from perceptual_ball.carrybox_fullbody_collision import FULL_BODY_COLLISION_PROFILE, SELF_COLLISION_FILTER_PAIRS
from perceptual_ball.carrybox_reward_geometry import reward_geometry, G1_ANCHORS, X2_ANCHORS
from . import carrybox as base
from .carrybox_walled import WalledCarryBoxEnv, state
from . import carrybox_walled as parent


def fixed_skill_ids(env_ids, num_envs, probabilities):
    """Persistent skill quotas from cumulative probabilities and environment midpoints."""
    if (len(probabilities) != 3 or any(not math.isfinite(p) or p < 0 for p in probabilities)
            or abs(sum(probabilities) - 1.) > 1.e-6 or num_envs < 1):
        raise ValueError('Invalid fixed skill allocation')
    edges = env_ids.new_tensor(probabilities, dtype=torch.float64).cumsum(0)[:-1]
    return torch.bucketize((env_ids.double() + .5) / num_envs, edges)

def action_bounds(env):
    """Training label only: raw Gaussian action bounds, paired with each environment."""
    term = env.action_manager.get_term('joint_pos')
    limits = env.scene['robot'].data.joint_pos_limits[:, term._joint_ids]
    low = ((limits[..., 0] - term._offset) / term._scale).clamp_min(-9.)
    high = ((limits[..., 1] - term._offset) / term._scale).clamp_max(9.)
    return torch.cat((low, high), -1).detach()

def reset_scene(env, env_ids):
    state(env).grasp_step = None
    skills = fixed_skill_ids(env_ids, env.num_envs, env.cfg.reset_skill_probabilities)
    parent.reset_scene(env, env_ids, skill_ids=skills)


def locomotion_stability(env):
    """Legacy revision17/18 diagnostic; not registered or used by revision19.

    The height factor is removed near the box so reaching down remains possible.
    All geometry is physical current state, independent of the reset skill.
    """
    robot = env.scene['robot'].data
    distance = parent.task_box_distance(env, env.scene['box'].data.root_pos_w - robot.root_link_pos_w)
    gravity = robot.projected_gravity_b
    upright = torch.exp(-10. * gravity[:, :2].square().sum(-1)) * (-gravity[:, 2]).clamp(0., 1.)
    height = robot.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
    standing = torch.exp(-20. * (.65 - height).clamp_min(0.).square())
    return upright * torch.where(distance > .7, standing, 1.)


def walk_task(env):
    return grasp_state(env)['walk_task']


def grasp_state(env):
    """Cache reward geometry once per control step; no policy observations."""
    s = state(env)
    if getattr(s, 'grasp_step', None) == env.common_step_counter:
        return s.grasp_terms
    if not hasattr(s, 'grasp_palms'):
        s.grasp_palms = env.scene['robot'].find_bodies(
            ['left_palm_link', 'right_palm_link'], preserve_order=True)[0]
        if len(s.grasp_palms) != 2:
            raise ValueError('Wall5 grasp rewards require both G1 palm link origins')
    robot = env.scene['robot'].data
    box = env.scene['box'].data
    delta = box.root_pos_w - robot.root_link_pos_w
    delta_xy = delta[:, :2]
    distance_xy = delta_xy.norm(dim=-1)
    towards = (delta_xy / distance_xy.clamp_min(1.e-6)[:, None] * robot.root_link_lin_vel_w[:, :2]).sum(-1)
    bearing = wrap_to_pi(torch.atan2(delta[:, 1], delta[:, 0]) - parent.heading(robot.root_link_quat_w)).abs()
    palms = robot.body_link_pos_w[:, s.grasp_palms] - box.root_pos_w[:, None]
    palms = quat_apply_inverse(box.root_quat_w[:, None].expand(-1, 2, -1), palms)
    force = torch.stack([env.scene[f'{side}_box_contact'].data.force_matrix_w
                         .flatten(1, -2).norm(dim=-1).amax(-1) for side in ('left', 'right')], -1)
    bottom, _, _ = base.lift_geometry(env)
    s.grasp_terms = grasp_components(delta, towards, bearing, palms,
        delta.new_tensor(env.cfg.scene.box.spawn.size) / 2, force, bottom, env.cfg.grasp_geometry)
    s.grasp_step = env.common_step_counter
    return s.grasp_terms


def grasp_task_reward(env, name):
    from .carrybox_x2_rewards import reward_terms
    g = grasp_state(env)
    if name == 'carryup_task':
        return g[name]
    if name == 'stable_grasp':
        s, robot = state(env), env.scene['robot'].data
        smooth = torch.exp(-.5 * robot.joint_vel[:, s.arm_ids].square().mean(-1)
                           - 2.e-4 * robot.joint_acc[:, s.arm_ids].square().mean(-1))
        return g['bilateral'] * smooth
    # Stabilize the arms AFTER bilateral grasp; do not punish the initial reach.
    return reward_terms(env)[name] * g['both_contacts']


def push_velocity_increment(env, env_ids, velocity_range):
    """Add a curriculum-scaled world COM velocity impulse (m/s and rad/s).

    Keep the inherited event's sampling order and ranges; full strength adds
    the sampled increment without clearing the robot's existing velocity.
    """
    ranges = torch.tensor([velocity_range[k] for k in ('x', 'y', 'z', 'roll', 'pitch', 'yaw')],
                          device=env.device)
    delta = ranges[:, 0] + torch.rand((len(env_ids), 6), device=env.device) * (ranges[:, 1] - ranges[:, 0])
    curriculum = state(env).curriculum
    effective = 0 if curriculum.anchor is None else max(0, curriculum.iteration - curriculum.anchor)
    scale = max(0., min(1., (effective - env.cfg.push_warmup_iterations) / env.cfg.push_ramp_iterations))
    if scale == 0.:
        return
    robot = env.scene['robot']
    robot.write_root_velocity_to_sim(robot.data.root_vel_w[env_ids] + scale * delta, env_ids=env_ids)


def critic_state(env):
    """Training-only state: proprio93, velocity3, box xyz3/rot6/size3, endpoints15.

    Velocity (m/s) and box pose are expressed in the pelvis link frame, not COM
    or camera coordinates. Size is the box's full local side lengths in metres.
    No visibility mask, sensor delay, AMP distance cap, or depth enters the critic.
    The final 15 values are the ordered palm/ankle/mid360 link origins relative
    to the pelvis link origin, in pelvis coordinates and metres (same as AMP).
    """
    if not hasattr(env, '_wall5_critic_bodies'):
        env._wall5_critic_bodies = env.scene['robot'].find_bodies(list(AMP_BODY_NAMES), preserve_order=True)[0]
        if len(env._wall5_critic_bodies) != 5:
            raise ValueError('Wall5 critic requires all five named link origins')
    robot, box = env.scene['robot'].data, env.scene['box'].data
    q = robot.root_link_quat_w
    linear = quat_apply_inverse(q, robot.root_link_lin_vel_w)
    xyz = quat_apply_inverse(q, box.root_pos_w - robot.root_link_pos_w)
    rotation = matrix_from_quat(quat_mul(quat_conjugate(q), box.root_quat_w))
    rot6 = rotation[..., :2].transpose(-1, -2).flatten(-2)
    size = xyz.new_tensor(env.cfg.scene.box.spawn.size).expand_as(xyz)
    relative_ends = robot.body_link_pos_w[:, env._wall5_critic_bodies] - robot.root_link_pos_w[:, None]
    ends = quat_apply_inverse(q[:, None].expand(-1, 5, -1), relative_ends).flatten(1)
    return torch.cat((base.proprioception(env), linear, xyz, rot6, size, ends), -1).detach()


def amp_frame(env):
    robot = env.scene['robot']
    if not hasattr(env, '_wall5_amp_bodies'):
        env._wall5_amp_bodies = robot.find_bodies(list(AMP_BODY_NAMES), preserve_order=True)[0]
        if len(env._wall5_amp_bodies) != 5:
            raise ValueError('Wall5 requires all five named AMP link origins')
        env._wall5_amp_joints = joint_mapping(robot.joint_names)
    data = robot.data
    root = data.root_link_pos_w
    return pack_task_frame(data.joint_pos[:, env._wall5_amp_joints], data.root_link_quat_w,
        data.body_link_pos_w[:, env._wall5_amp_bodies] - root[:, None], data.root_link_lin_vel_w,
        data.root_link_ang_vel_b, env.scene['box'].data.root_pos_w - root)


def pose_visible(env, depth, pose):
    """Nearest Box hit surviving corruption, with its centre inside optical depth range."""
    camera = env.scene['depth_camera']
    if not hasattr(env, '_wall5_box_mesh'):
        env._wall5_box_mesh = next(i for i, m in enumerate(camera.mesh_manifest) if m['root'].endswith('/Box'))
    hits = camera.data.output['mesh_id'][..., 0]
    metres = getattr(getattr(env, 'cfg', None), 'depth_in_metres', False)
    near, far = (.1, 3.) if metres else (.1/3., 1.)
    visible = ((hits == env._wall5_box_mesh) & (depth < far) & (depth >= near)).flatten(1).any(-1)
    return visible & (pose[:, 2] >= .1) & (pose[:, 2] < 3.) & torch.isfinite(pose).all(-1)


def tipped(env):
    roll, pitch, _ = euler_xyz_from_quat(env.scene['robot'].data.root_quat_w)
    return (wrap_to_pi(roll).abs() > .5) | (wrap_to_pi(pitch).abs() > 1.1)


class Wall5CarryBoxEnv(WalledCarryBoxEnv):
    amp_warmup_steps = 0

    @property
    def depth_contract(self):
        """The actor and exported policy consume the same depth units."""
        metres = self.cfg.depth_in_metres
        return dict(schema=1, output='optical_z_metres' if metres else 'optical_z_over3',
                    units='metres' if metres else 'normalized',
                    normalization='none' if metres else 'divide_by_3',
                    clip_range_m=[.1, 3.], invalid_depth_m=3.,
                    input_range=[.1, 3.] if metres else [.1/3., 1.],
                    missing_value=3. if metres else 1.,
                    shape=[4, 27, 48], history_order='oldest_to_newest',
                    gaussian_std_m=self.cfg.depth_noise_std_m,
                    stereo_sigma_m=[self.cfg.depth_stereo_near_m, self.cfg.depth_stereo_far_m],
                    label_timing='capture_then_paired_delay_freeze_reset')

    def step(self, action):
        # Attribute terminal transitions to their old skill, before any reset.
        skills = state(self).skills.clone()
        defaults = state(self).default_reset.clone()
        result = super().step(action)
        log = result[-1].setdefault('log', {})
        reset_state = state(self)
        if hasattr(reset_state, 'reset_counts'):
            for i, name in enumerate(('default', 'loco_rsi', 'pickup_rsi', 'hold_rsi')):
                log[f'Reset/{name}_fraction'] = reset_state.reset_counts[i] / reset_state.reset_counts.sum().clamp_min(1)
            log['Sampling/default_transition_fraction'] = defaults.float().mean()
        names = self.reward_manager.active_terms
        for skill, name in enumerate(('loco', 'pickup', 'hold')):
            mask = (skills == skill).float()
            count = mask.sum().clamp_min(1.)
            log[f'Sampling/{name}_transition_fraction'] = mask.mean()
            log[f'Reward/{name}_task_per_step'] = (result[1] * mask).sum() / count
            if skill == 0:
                terms = (self.reward_manager._step_reward * mask[:, None]).sum(0) / count * self.step_dt
                for key in ('walk_task', 'carryup_task', 'standup_task', 'action_rate', 'torques', 'alive'):
                    log[f'Reward/loco_{key}_per_step'] = terms[names.index(key)]
                robot = self.scene['robot'].data
                # Post-reset kinematics are excluded from these continuous diagnostics.
                active = mask * (~(result[2] | result[3])).float()
                denominator = active.sum().clamp_min(1.)
                speed = robot.root_link_lin_vel_w[:, :2].norm(dim=-1)
                delta = self.scene['box'].data.root_pos_w - robot.root_link_pos_w
                distance = parent.task_box_distance(self, delta)
                log['Motion/loco_survivor_speed_mps'] = (speed * active).sum() / denominator
                log['Motion/loco_survivor_box_distance_m'] = (distance * active).sum() / denominator
                log['Motion/loco_survivor_box_distance_xy_m'] = (delta[:, :2].norm(dim=-1) * active).sum() / denominator
                # The reward cache describes the pre-reset transition; use the
                # old-skill mask so final contacts are not replaced by RSI.
                grasp = getattr(state(self), 'grasp_terms', None)
                if grasp is not None:
                    for key in ('reach', 'bilateral', 'lift', 'crowding'):
                        log[f'Grasp/loco_{key}'] = (grasp[key] * mask).sum() / count
                    log['Grasp/loco_both_contact_fraction'] = (grasp['both_contacts'] * mask).sum() / count
                    log['Grasp/loco_palm_surface_distance_m'] = (grasp['surface_distance'].mean(-1) * mask).sum() / count
        return result

    def _reset_idx(self, env_ids):
        # Capture BEFORE the parent resets physics; timeout values must describe
        # the terminated state, never the newly sampled reference initialization.
        terminal = (critic_state(self)[env_ids].clone()
                    if getattr(self, '_carrybox_in_step', False) else None)
        super()._reset_idx(env_ids)
        # Multiple causes may coincide; this is physical tilt at episode end,
        # not an exclusive attribution of the reset to a single cause.
        log = self.extras['log']
        for name in ('loco', 'pickup', 'hold'):
            log[f'Skill/{name}_tilt_at_episode_end_fraction'] = log.pop(f'Skill/{name}_tipped_fraction')
        if len(env_ids) and hasattr(state(self), 'reset_ground_correction'):
            shift = state(self).reset_ground_correction[env_ids]
            log['Reset/ground_correction_mean_m'] = shift.mean()
            log['Reset/ground_correction_max_m'] = shift.max()
        if terminal is not None:
            self._carrybox_terminal['obs']['critic_state'] = terminal

    def terminal_frame(self, group):
        return amp_frame(self) if group == 'amp' else super().terminal_frame(group)

    def checkpoint_contract(self):
        contract = super().checkpoint_contract()
        library = state(self).library
        reference_hash = (library.metadata['manifest_sha256'] if library is not None else
                          hashlib.sha256((Path(self.cfg.reference_motion_dataset) / 'amp_manifest.json').read_bytes()).hexdigest())
        contract.update(migration_revision=27, physical_parent='physhsi_g1_collision_hybrid_reset_v24',
                        collision_profile=FULL_BODY_COLLISION_PROFILE,
                        self_collisions=self.cfg.scene.robot.spawn.articulation_props.enabled_self_collisions,
                        shoulder_colliders='visual_mesh_convex_hull',
                        amp_frame_schema=WALL5_FEATURE_SCHEMA, amp_shape=[10, 60],
                        amp_history='repeat_reset_frame_reward_and_training_from_step1')
        contract['self_collision_filter_pairs'] = [list(pair) for pair in SELF_COLLISION_FILTER_PAIRS]
        contract['grasp_reward'] = dict(self.cfg.grasp_geometry)
        contract['grasp_reward']['hand_points'] = 'left_right_palm_link_origins_in_oriented_box_frame'
        contract['grasp_reward']['contact_source'] = 'rubber_hand_force_filtered_to_Box_only'
        contract['grasp_reward']['arm_smoothing_gate'] = 'bilateral_box_contact'
        contract['amp_dataset_profile'] = 'full_three_pickups_192_178_129_no_trimming'
        contract['amp_manifest_sha256'] = hashlib.sha256((Path(AMP_DATASET_PATH) / 'amp_manifest.json').read_bytes()).hexdigest()
        held_reference = getattr(self.cfg, 'held_box_reference_reset', False)
        contract.update(box_reset_profile=(GROUND_RESET_PROFILE + '_except_reference_hold_v1' if held_reference else GROUND_RESET_PROFILE),
                        held_box_reference_reset=held_reference,
                        ground_box_reset=self.cfg.ground_box_reset,
                        ground_pickup_reset_frame_range=list(self.cfg.ground_pickup_reset_frame_range),
                        support_platform=self.cfg.scene.platform is not None,
                        reference_dataset_profile='findbox_ground_pickup_v1',
                        reference_manifest_sha256=reference_hash)
        contract.update(reference_velocity='source_position_difference_pelvis_link', failure_reward='none_x2_recipe',
                        roll_termination='abs_roll_gt_0.5', aux_supervision='all_paired_frames_xyz_rot6_visibility_diagnostic_only_v1',
                        aux_target_shape=10, early_failure_penalty_weight=0., roll_limit=.5,
                        height_termination_terms=list(self.cfg.height_termination_terms),
                        failure_diagnostics='pre_reset_physical_causes_per_completed_skill_episode_multi_label_v20',
                        reset_skill_probabilities=list(self.cfg.reset_skill_probabilities))
        contract.update(actor_observations='proprio93x4_depth4x27x48_no_privileged',
                        critic_observations='current_proprio93_pelvis_link_linvel3_box_local_xyz3_rot6_size3_ends15_v2',
                        critic_shape=123, critic_network='independent_mlp_512_256_256_no_depth',
                        critic_endpoint_names=list(AMP_BODY_NAMES),
                        critic_endpoint_frame='pelvis_link_origin_relative_positions_metres',
                        critic_terminal='pre_reset_current_state',
                        box_rotation6='first_two_columns_of_pelvis_inverse_times_box')
        contract.update(reset_assignment='fixed_env_midpoint_skill_quota_v1',
                        action_bounds_supervision='paired_raw_physical_limits_offset_scale_intersect_wrapper9_58_v1',
                        locomotion_feedback='approach_then_0.52m_stance_plus_survival_v27')
        contract['survival_reward'] = dict(weight=self.cfg.rewards.alive.weight, units='per_second',
            gating='not_terminated_timeouts_alive', posture_target=None)
        contract['reward_geometry'] = dict(reward_geometry(self))
        contract['depth_observation'] = self.depth_contract
        contract['reward_geometry_calibration'] = {
            'g1_anchors_m': dict(G1_ANCHORS), 'x2_anchors_m': dict(X2_ANCHORS),
            'x2_anchor_source': 'user_corrected_head_yaw_link_reference_20261021_not_local_fk',
            'ground_box_center_m': .125,
            'method': 'grounded_foot_hull_reference_fk_equal_clip_medians_gravity_xy_lt_0.2',
            'height_frame': 'world_minus_environment_ground',
            'standup_velocity': 'pelvis_com_in_pelvis_frame', 'search_yaw_rate': 'pelvis_frame',
            'height_exponents': 'inverse_length_scale',
            'strict_lift_hold_metric': 'unchanged_contact_clearance_upright_speed_0.5s',
        }
        contract['task_box_distance'] = {
            'metric': 'xyz_l2' if self.cfg.task_box_distance_3d else 'xy_l2',
            'points': 'pelvis_link_origin_to_box_center', 'threshold_m': reward_geometry(self)['near_distance'],
            'approach_velocity_direction': 'normalized_xy', 'amp_box_cap': 'unchanged_xy_0.7',
        }
        contract['push_velocity_semantics'] = 'current_world_com_velocity_plus_curriculum_scaled_increment_v1'
        contract['contact_materials'] = {
            name: {key: getattr(material, key) for key in
                   ('static_friction', 'dynamic_friction', 'restitution',
                    'friction_combine_mode', 'restitution_combine_mode')}
            for name, material in (('simulation_default', self.cfg.sim.physics_material),
                                   ('ground', self.cfg.scene.ground.spawn.physics_material))
        }
        from perceptual_ball.carrybox_physhsi import COLLISION_PROFILE, RESET_PROFILE, hybrid_probabilities
        probabilities = hybrid_probabilities(self.cfg.reset_reference_probability, self.cfg.reset_skill_probabilities)
        contract.update(collision_profile=COLLISION_PROFILE, shoulder_colliders='original_urdf_capsules',
                        self_collision_filter_pairs=[], reference_ground_clearance='G1_collision_hull_min_5mm_upward_only_after_randomized_joint_reset',
                        paired_reference_ground_shift='robot_box_active_support_same_dz',
                        head_reference='mid360_link_origin', reference_velocity='world_com_uniform_rsi0.2_default0.5',
                        reset_assignment=RESET_PROFILE, box_reset_profile='findbox_ground_loco_full_reference_pickup_hold',
                        reference_dataset_profile='findbox_full_three_pickups_v1', ground_pickup_reset_frame_range=None,
                        reset_default_probability=probabilities[0], reset_reference_probability=self.cfg.reset_reference_probability,
                        reset_total_probabilities=list(probabilities),
                        reset_quota_scope='fixed_global_env_id_default_loco_pickup_hold_initialization_only',
                        reference_time='continuous_uniform_full_clip', joint_reset_noise_rad=.1,
                        joint_reset_velocity='source_joint_velocity', joint_reset_limits='0.9_urdf_range_soft_limits', collision_reward='disabled_physhsi',
                        physics_action_delay={'physics_dt': self.physics_dt, 'slots': 5, 'range_s': [0., .02],
                                              'reset_fill': 'final_reset_joint_position', 'update': 'each_physics_step'},
                        termination_profile={'root_height_m': .2, 'mid360_height_m': .6, 'hip_yaw_height_m': .15,
                                             'box_xy_speed_mps': 3., 'roll_rad': .5, 'pitch_rad': 1.1,
                                             'box_tilt': False, 'success_reset': False},
                        failure_diagnostics='pre_reset_height_causes_and_tilt_at_episode_end_v26')
        return contract
