"""Wall5 AMP observation contract and versioned full-body collision geometry."""
import hashlib
import torch
from isaaclab.utils.math import (euler_xyz_from_quat, wrap_to_pi, quat_apply_inverse,
                               quat_mul, quat_conjugate, matrix_from_quat)
from perceptual_ball.carrybox_amp import joint_mapping
from pathlib import Path
from perceptual_ball.carrybox_wall5 import pack_task_frame, AMP_BODY_NAMES, WALL5_FEATURE_SCHEMA, GROUND_RESET_PROFILE
from perceptual_ball.carrybox_fullbody_collision import FULL_BODY_COLLISION_PROFILE
from . import carrybox as base
from .carrybox_walled import WalledCarryBoxEnv, state


def critic_state(env):
    """Training-only current state: proprio93, pelvis velocity3, box xyz3/rot6/size3.

    Velocity (m/s) and box pose are expressed in the pelvis link frame, not COM
    or camera coordinates. Size is the box's full local side lengths in metres.
    No visibility mask, sensor delay, AMP distance cap, or depth enters the critic.
    """
    robot, box = env.scene['robot'].data, env.scene['box'].data
    q = robot.root_link_quat_w
    linear = quat_apply_inverse(q, robot.root_link_lin_vel_w)
    xyz = quat_apply_inverse(q, box.root_pos_w - robot.root_link_pos_w)
    rotation = matrix_from_quat(quat_mul(quat_conjugate(q), box.root_quat_w))
    rot6 = rotation[..., :2].transpose(-1, -2).flatten(-2)
    size = xyz.new_tensor(env.cfg.scene.box.spawn.size).expand_as(xyz)
    return torch.cat((base.proprioception(env), linear, xyz, rot6, size), -1).detach()


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
    visible = ((hits == env._wall5_box_mesh) & (depth < 1.) & (depth >= .1/3.)).flatten(1).any(-1)
    return visible & (pose[:, 2] >= .1) & (pose[:, 2] < 3.) & torch.isfinite(pose).all(-1)


def tipped(env):
    roll, pitch, _ = euler_xyz_from_quat(env.scene['robot'].data.root_quat_w)
    return (wrap_to_pi(roll).abs() > .8) | (wrap_to_pi(pitch).abs() > 1.1)


class Wall5CarryBoxEnv(WalledCarryBoxEnv):
    amp_warmup_steps = 0

    def _reset_idx(self, env_ids):
        # Capture BEFORE the parent resets physics; timeout values must describe
        # the terminated state, never the newly sampled reference initialization.
        terminal = (critic_state(self)[env_ids].clone()
                    if getattr(self, '_carrybox_in_step', False) else None)
        super()._reset_idx(env_ids)
        if terminal is not None:
            self._carrybox_terminal['obs']['critic_state'] = terminal

    def terminal_frame(self, group):
        return amp_frame(self) if group == 'amp' else super().terminal_frame(group)

    def checkpoint_contract(self):
        contract = super().checkpoint_contract()
        library = state(self).library
        reference_hash = (library.metadata['manifest_sha256'] if library is not None else
                          hashlib.sha256((Path(self.cfg.reference_motion_dataset) / 'amp_manifest.json').read_bytes()).hexdigest())
        contract.update(migration_revision=14, physical_parent='wall5_full_body_mixed_reset_v1',
                        collision_profile=FULL_BODY_COLLISION_PROFILE,
                        self_collisions=self.cfg.scene.robot.spawn.articulation_props.enabled_self_collisions,
                        shoulder_colliders='visual_mesh_convex_hull',
                        amp_frame_schema=WALL5_FEATURE_SCHEMA, amp_shape=[10, 60],
                        amp_history='repeat_reset_frame_reward_and_training_from_step1')
        held_reference = getattr(self.cfg, 'held_box_reference_reset', False)
        contract.update(box_reset_profile=(GROUND_RESET_PROFILE + '_except_reference_hold_v1' if held_reference else GROUND_RESET_PROFILE),
                        held_box_reference_reset=held_reference,
                        ground_box_reset=self.cfg.ground_box_reset,
                        ground_pickup_reset_frame_range=list(self.cfg.ground_pickup_reset_frame_range),
                        support_platform=self.cfg.scene.platform is not None,
                        reference_dataset_profile='findbox_ground_pickup_v1',
                        reference_manifest_sha256=reference_hash)
        contract.update(reference_velocity='source_position_difference_pelvis_link', failure_reward='current_fell_or_tipped_exclude_timeout_dt_scaled',
                        roll_termination='abs_roll_gt_0.8', aux_supervision='visible_box_hit_and_optical_range_paired_mask_v1',
                        aux_target_shape=10, early_failure_penalty_weight=-10., roll_limit=.8,
                        reset_skill_probabilities=list(self.cfg.reset_skill_probabilities))
        contract.update(actor_observations='proprio93x4_depth4x27x48_no_privileged',
                        critic_observations='current_proprio93_pelvis_link_linvel3_box_local_xyz3_rot6_size3_v1',
                        critic_shape=108, critic_network='independent_mlp_512_256_256_no_depth',
                        critic_terminal='pre_reset_current_state',
                        box_rotation6='first_two_columns_of_pelvis_inverse_times_box')
        return contract
