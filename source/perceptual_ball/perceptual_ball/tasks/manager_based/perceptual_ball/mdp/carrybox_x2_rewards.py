"""X2 handoff reward equations with explicit G1 frames and box-filtered hand forces.

All returned values are unweighted; RewardManager applies weight * policy dt once.
Truth here is reward-only and never enters policy/value/AMP observations.
"""
import torch
from isaaclab.utils.math import quat_apply_inverse, wrap_to_pi
from . import carrybox as base


def reward_terms(env):
    from .carrybox_walled import state, heading, head_height
    s = state(env)
    if getattr(s, 'reward_step', None) == env.common_step_counter:
        return s.reward_terms
    robot, box = env.scene['robot'].data, env.scene['box'].data
    ground = env.scene.env_origins[:, 2]
    delta = box.root_pos_w[:, :2] - robot.root_pos_w[:, :2]
    distance = delta.norm(dim=-1)
    torso_q = robot.body_quat_w[:, s.torso]
    linear_w = robot.body_lin_vel_w[:, s.torso]
    linear_b = quat_apply_inverse(torso_q, linear_w)
    angular_b = quat_apply_inverse(torso_q, robot.body_ang_vel_w[:, s.torso])
    gravity = quat_apply_inverse(torso_q, robot.GRAVITY_VEC_W)
    towards = (delta / distance.clamp_min(1.e-6)[:, None] * linear_w[:, :2]).sum(-1)
    bearing = wrap_to_pi(torch.atan2(delta[:, 1], delta[:, 0]) - heading(robot.root_quat_w)).abs()
    walk = torch.exp(-5 * (.85 - towards).square()) + .5 * torch.exp(-.75 * bearing)
    walk = torch.where(distance < .7, 1.5, walk)
    hands = robot.body_pos_w[:, s.hands].mean(1)
    hand_sq = (hands - box.root_pos_w).square().sum(-1)
    force = torch.stack([
        env.scene[f'{side}_box_contact'].data.force_matrix_w.flatten(1, -2).norm(dim=-1).amax(-1)
        for side in ('left', 'right')], -1)
    contact = 1 - torch.exp(-.5 * force)
    box_z = box.root_pos_w[:, 2] - ground
    root_z = robot.root_pos_w[:, 2] - ground
    head_z = head_height(env)
    hand_contact = contact.mean(-1) * (hand_sq <= .3)
    carryup = (.7 * torch.exp(-3 * hand_sq) + 1.5 * hand_contact
               + 1.5 * torch.exp(-3 * (.64 - box_z).clamp_min(0))) * (distance <= .7)
    immediate_success = (box_z > .6) & (gravity[:, :2].norm(dim=-1) < .2) & (head_z > .8) & (hand_sq < .3**2)
    gate = ((root_z - .50) / .16).clamp(0, 1)
    standup = (torch.exp(-8 * (.66-root_z).clamp_min(0))
               + torch.exp(-8 * (.85-head_z).clamp_min(0))
               + gate * (torch.exp(-.3 * linear_b.abs().sum(-1))
                         + torch.exp(-.3 * angular_b.abs().sum(-1))
                         + torch.exp(-box.root_lin_vel_w.norm(dim=-1))
                         * torch.exp(-.3 * box.root_ang_vel_w.norm(dim=-1)))) * immediate_success
    arm_vel, arm_acc = robot.joint_vel[:, s.arm_ids], robot.joint_acc[:, s.arm_ids]
    crouched = (distance < .7) & (root_z < .60) & (box_z < .58)
    proximity = torch.exp(-20 * hand_sq)
    stable = (torch.exp(-.5 * arm_vel.square().mean(-1) - 2e-4 * arm_acc.square().mean(-1))
              * (.5 * proximity + .5 * contact.prod(-1) * proximity) * crouched)
    s.reward_terms = dict(
        walk_task=walk, carryup_task=carryup, standup_task=standup,
        slow_pickup=robot.joint_vel.square().sum(-1) * ((distance < .7) & (box_z < .55)),
        stable_grasp=stable,
        arm_speed_pickup=(arm_vel.abs()-1.).clamp_min(0).square().mean(-1) * crouched,
        arm_acc_pickup=(arm_acc.abs()-20.).clamp_min(0).square().mean(-1) * crouched,
        grip_force_cap=(force-7.).clamp_min(0).mean(-1) * (hand_sq <= .3**2))
    s.reward_step = env.common_step_counter
    # Separate stricter G1 metric (contact, clearance, upright and 0.5s hold).
    s.achieved |= base.lift_success(env)
    return s.reward_terms


def task_reward(env, name):
    return reward_terms(env)[name]
