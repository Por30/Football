# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Ball-serving state machine, adapted from the x2_kickball_depth_v3 handoff recipe
(/home/cao/perceptual_ball/kickball). Within a single episode the ball is served repeatedly at
the robot (recorded "anchor" pose), rolls in, and either gets kicked or rolls past/away/to a
stop, after which it is re-served a few steps later -- giving many kick attempts per episode
instead of one.

State is held on `env._kickball` (a `KickballState` instance attached by the `setup_kickball_state`
startup event) rather than as attributes on any single reward/observation term, since many
different reward terms (approach, return-speed, kick bonus, miss penalty) and one termination
term (walked away from anchor) all need to read the same per-env state, and it must be advanced
exactly once per step, before any of those terms run (see `tick_kickball_state`).

Reset also applies Reference State Initialization (RSI, see `_apply_rsi`): most resets overwrite
the plain standing pose with a random frame from the real kick clips, so the policy starts many
episodes already mid-kick instead of only ever seeing that from wherever it wanders on its own.
"""

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils.math import quat_apply_inverse

from .amp import KICK_MOTION_CLIP_PATHS, MotionLibrary

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv

BALL_RADIUS = 0.11

# Reference State Initialization (RSI): most resets start the robot mid-reference-motion (a
# random frame of the real kick clips) instead of from the default stance, so the policy sees
# (and can imitate) in-progress kicking poses from the very first step of many episodes, not
# just after it has already learned to approach the ball on its own.
RSI_PROBABILITY = 0.8

SERVE_DISTANCE_RANGE = (1.3, 2.0)
SERVE_BEARING_RANGE = (-0.35, 0.35)
SERVE_AIM_OFFSET_RANGE = (-0.25, 0.25)
SERVE_SPEED_RANGE = (0.4, 0.8)

BALL_END_MAX_DIST_FROM_ANCHOR = 3.0
BALL_END_MIN_FORWARD_PROJECTION = -0.3
BALL_END_MIN_SPEED = 0.15
STEPS_BETWEEN_SERVES = 20

KICK_STRIKE_IMPULSE_THRESHOLD = 0.15
KICK_SUCCESS_MAX_DIST = 2.0
KICK_SUCCESS_MIN_RETURN_SPEED = 0.4

# The two kicking feet, in skill order: skill 0 == kick_left, 1 == kick_right. This is also the
# order of `mdp.amp.KICK_MOTION_CLIP_PATHS` (kick_left.pt, kick_right.pt) and of the AMP
# discriminators and critics, so one skill index selects the matching foot, reference clip,
# discriminator and value function everywhere.
KICK_FOOT_BODY_NAMES = ["left_ankle_roll_link", "right_ankle_roll_link"]
NUM_SKILLS = len(KICK_FOOT_BODY_NAMES)

# Left/right skill routing, per the v11 spec: an EMA of the ball's lateral position in the
# robot's own frame, with a dead band so a ball near the centre line does not flip the skill
# every step. The label is *derived from where the ball is*, not commanded -- the policy never
# sees it (it is not in the actor observation), it only selects which AMP discriminator grades
# the motion and which critic values the state.
SKILL_EMA_ALPHA = 0.2  # ema <- 0.8 * ema + 0.2 * ball_y
SKILL_DEAD_BAND = 0.1  # m; outside it the label switches, inside it the previous label holds

# How close the nearer foot has to be to the ball for a velocity jump to count as a kick.
# The impulse test alone calls any collision a kick, including the ball bouncing off a fallen
# robot's torso: over 400 steps of a passive robot, 50 such "kicks" were detected, with the
# nearest foot 0.47-1.19 m away (median 0.78 m) and none of them inside 0.30 m. A real foot
# strike is ~0.2 m centre-to-centre (0.11 m ball radius plus roughly 0.1 m from the ankle_roll
# link's origin to the striking surface), so 0.30 m clears every genuine kick and none of the
# body collisions. This also protects the left/right attribution: `argmin` over the two feet is
# meaningful at 0.2 m and a coin flip at 0.8 m.
KICK_FOOT_CONTACT_MAX_DIST = 0.30


def _rand_range(low: float, high: float, shape, device) -> torch.Tensor:
    return torch.rand(shape, device=device) * (high - low) + low


class KickballState:
    """Per-env ball-serving / kick-detection state, persisted on the environment instance."""

    def __init__(
        self,
        env: ManagerBasedRLEnv,
        robot_cfg: SceneEntityCfg,
        ball_cfg: SceneEntityCfg,
        rsi_probability: float = RSI_PROBABILITY,
        strike_gated_return_speed: bool = False,
        require_foot_contact: bool = False,
    ):
        self.robot: Articulation = env.scene[robot_cfg.name]
        self.ball: RigidObject = env.scene[ball_cfg.name]
        self.env_origins = env.scene.env_origins
        self.env = env
        self.serve_speed_range = SERVE_SPEED_RANGE
        self.serve_speed_override = None  # play-only; never serialized as training curriculum
        self.serve_distance_range = SERVE_DISTANCE_RANGE
        self.rsi_probability = rsi_probability
        self.strike_gated_return_speed = strike_gated_return_speed
        self.require_foot_contact = require_foot_contact

        # resolved one name at a time (not as one regex) because the command index has to mean
        # "left" and "right" specifically, and a regex resolves to whatever order the
        # articulation happens to list its bodies in
        foot_ids = []
        for body_name in KICK_FOOT_BODY_NAMES:
            foot_cfg = SceneEntityCfg(robot_cfg.name, body_names=[body_name])
            foot_cfg.resolve(env.scene)
            foot_ids.append(foot_cfg.body_ids[0])
        self.foot_body_ids = torch.tensor(foot_ids, device=env.device, dtype=torch.long)
        # a separate MotionLibrary instance from BallRegressionPPO's (that one lives on the
        # algorithm, which the env has no handle to) -- same two clips, used here for RSI instead
        # of expert-batch sampling. Loading it twice costs a trivial amount of memory (two ~5s
        # clips) for a clean separation between env logic and RL-algorithm internals.
        self.motion_library = MotionLibrary(KICK_MOTION_CLIP_PATHS, device=env.device)
        if self.robot.joint_names != self.motion_library.joint_names:
            raise ValueError("G1 joint order differs from AMP clip metadata")
        device = env.device
        n = env.num_envs

        self.anchor_xy = torch.zeros(n, 2, device=device)
        self.anchor_yaw = torch.zeros(n, device=device)
        self.ball_active = torch.zeros(n, dtype=torch.bool, device=device)
        self.ball_kicked = torch.zeros(n, dtype=torch.bool, device=device)
        self.steps_since_ball_ended = torch.zeros(n, dtype=torch.long, device=device)
        self.prev_ball_vel_xy = torch.zeros(n, 2, device=device)
        # Left/right skill routing state. Deliberately NOT cleared on reset (matching the v11
        # spec): the EMA is a property of the running policy's situation, not of an episode, and
        # zeroing it would put every fresh episode back in the dead band on the right-hand label.
        self.ball_y_ema = torch.zeros(n, device=device)
        self.skill_is_left = torch.zeros(n, dtype=torch.bool, device=device)

        # one-step pulses, refreshed every tick, consumed by reward terms the same step
        self.kick_success_flag = torch.zeros(n, dtype=torch.bool, device=device)
        self.just_missed = torch.zeros(n, dtype=torch.bool, device=device)
        self.ball_return_speed = torch.zeros(n, device=device)
        self.foot_ball_dist = torch.zeros(n, len(KICK_FOOT_BODY_NAMES), device=device)

    def reset(self, env_ids: torch.Tensor) -> None:
        if len(env_ids) == 0:
            return
        self._apply_rsi(env_ids)
        root_pos = self.robot.data.root_pos_w[env_ids, :2]
        root_yaw = _yaw_from_quat(self.robot.data.root_quat_w[env_ids])
        self.anchor_xy[env_ids] = root_pos
        self.anchor_yaw[env_ids] = root_yaw
        self.ball_kicked[env_ids] = False
        self.ball_active[env_ids] = False
        self.steps_since_ball_ended[env_ids] = STEPS_BETWEEN_SERVES  # serve immediately below
        self.prev_ball_vel_xy[env_ids] = 0.0
        self.ball_y_ema[env_ids] = 0.0
        self.skill_is_left[env_ids] = False
        self.kick_success_flag[env_ids] = False
        self.just_missed[env_ids] = False
        self.ball_return_speed[env_ids] = 0.0
        self._serve(env_ids)

    def _apply_rsi(self, env_ids: torch.Tensor) -> None:
        """For ~`self.rsi_probability` of `env_ids`, overwrite the standing pose the reset EventCfg
        terms (reset_robot_joints / reset_robot_root_yaw) already wrote with a random frame from
        the real kick clips. The rest keep that default-stance state as-is."""
        if self.rsi_probability <= 0.0:
            return
        is_rsi = torch.rand(len(env_ids), device=env_ids.device) < self.rsi_probability
        rsi_ids = env_ids[is_rsi]
        if len(rsi_ids) == 0:
            return

        root_pos, root_quat, root_lin_vel, root_ang_vel, joint_pos, joint_vel = self.motion_library.get_motion_state(
            len(rsi_ids)
        )
        root_pos = root_pos + self.env_origins[rsi_ids]

        self.robot.write_root_pose_to_sim(torch.cat([root_pos, root_quat], dim=-1), rsi_ids)
        self.robot.write_root_velocity_to_sim(torch.cat([root_lin_vel, root_ang_vel], dim=-1), rsi_ids)
        self.robot.write_joint_state_to_sim(joint_pos, joint_vel, env_ids=rsi_ids)

    def _sample_serve_speed(self, env_ids):
        if self.serve_speed_override is not None:
            self.serve_speed_range = self.serve_speed_override
        return _rand_range(*self.serve_speed_range, (len(env_ids),), self.anchor_xy.device)

    def _serve(self, env_ids: torch.Tensor) -> None:
        device = self.anchor_xy.device
        n = len(env_ids)
        anchor_xy = self.anchor_xy[env_ids]
        anchor_yaw = self.anchor_yaw[env_ids]

        distance = _rand_range(*self.serve_distance_range, (n,), device)
        bearing = _rand_range(*SERVE_BEARING_RANGE, (n,), device)
        theta = anchor_yaw + bearing
        ball_xy = anchor_xy + distance.unsqueeze(-1) * torch.stack([theta.cos(), theta.sin()], dim=-1)

        to_anchor = anchor_xy - ball_xy
        to_anchor_unit = to_anchor / to_anchor.norm(dim=-1, keepdim=True).clamp(min=1.0e-6)
        perp = torch.stack([-to_anchor_unit[:, 1], to_anchor_unit[:, 0]], dim=-1)
        aim_offset = _rand_range(*getattr(self, "serve_aim_offset_range", SERVE_AIM_OFFSET_RANGE), (n,), device)
        aim_xy = anchor_xy + perp * aim_offset.unsqueeze(-1)

        v_dir = aim_xy - ball_xy
        v_dir = v_dir / v_dir.norm(dim=-1, keepdim=True).clamp(min=1.0e-6)
        speed = self._sample_serve_speed(env_ids)
        lin_vel_xy = v_dir * speed.unsqueeze(-1)

        root_pose = torch.zeros(n, 7, device=device)
        root_pose[:, 0:2] = ball_xy
        root_pose[:, 2] = BALL_RADIUS
        root_pose[:, 3] = 1.0  # identity quat (w,x,y,z)
        self.ball.write_root_pose_to_sim(root_pose, env_ids)

        root_vel = torch.zeros(n, 6, device=device)
        root_vel[:, 0:2] = lin_vel_xy
        root_vel[:, 3] = -lin_vel_xy[:, 1] / BALL_RADIUS
        root_vel[:, 4] = lin_vel_xy[:, 0] / BALL_RADIUS
        self.ball.write_root_velocity_to_sim(root_vel, env_ids)

        self.ball_active[env_ids] = True
        self.ball_kicked[env_ids] = False
        self.steps_since_ball_ended[env_ids] = 0
        self.prev_ball_vel_xy[env_ids] = lin_vel_xy
        local_ball = torch.cat((ball_xy - self.robot.data.root_pos_w[env_ids, :2], torch.zeros(n, 1, device=device)), -1)
        self.ball_y_ema[env_ids] = quat_apply_inverse(self.robot.data.root_quat_w[env_ids], local_ball)[:, 1]
        self.skill_is_left[env_ids] = self.ball_y_ema[env_ids] >= 0
        self.kick_success_flag[env_ids] = False
        self.just_missed[env_ids] = False
        self.ball_return_speed[env_ids] = 0.0

    def _update_skill(self, ball_xy: torch.Tensor) -> None:
        """Route left/right from the ball's lateral offset in the robot's own frame.

        `ball_y > 0` means the ball is on the robot's left, which calls for the left-foot skill.
        The EMA smooths out the per-step jitter of a rolling ball and the dead band keeps a ball
        near the centre line from flipping the label (and therefore the discriminator and the
        critic) every step -- inside the band the previous label simply holds.
        """
        to_ball = torch.cat([ball_xy - self.robot.data.root_pos_w[:, :2], torch.zeros_like(ball_xy[:, :1])], dim=-1)
        ball_y = quat_apply_inverse(self.robot.data.root_quat_w, to_ball)[:, 1]

        self.ball_y_ema = (1.0 - SKILL_EMA_ALPHA) * self.ball_y_ema + SKILL_EMA_ALPHA * ball_y
        self.skill_is_left = torch.where(
            self.ball_y_ema > SKILL_DEAD_BAND,
            torch.ones_like(self.skill_is_left),
            torch.where(self.ball_y_ema < -SKILL_DEAD_BAND, torch.zeros_like(self.skill_is_left), self.skill_is_left),
        )

    @property
    def skill_ids(self) -> torch.Tensor:
        """Per-env skill index: 0 == kick_left, 1 == kick_right."""
        return torch.where(self.skill_is_left, 0, 1)

    def tick(self) -> None:
        """Advance the state machine by one control step. Must run before any reward term
        that reads kick_success_flag/just_missed/ball_return_speed/ball_active this step."""
        ball_xy = self.ball.data.root_pos_w[:, :2]
        ball_vel_xy = self.ball.data.root_lin_vel_w[:, :2]
        robot_xy = self.robot.data.root_pos_w[:, :2]

        impulse = (ball_vel_xy - self.prev_ball_vel_xy).norm(dim=-1)
        struck_this_step = impulse > KICK_STRIKE_IMPULSE_THRESHOLD

        outward_dir = ball_xy - self.anchor_xy
        outward_dir = outward_dir / outward_dir.norm(dim=-1, keepdim=True).clamp(min=1.0e-6)
        self.ball_return_speed = (ball_vel_xy * outward_dir).sum(dim=-1)
        # Which foot is where. There is no contact sensor on the ball and the strike is detected
        # from the ball's own velocity jump (see above), so both the "was this a kick at all"
        # test and the "which foot did it" attribution come from foot-to-ball distance at the
        # step the jump is seen.
        foot_pos = self.robot.data.body_link_pos_w[:, self.foot_body_ids, :]
        self.foot_ball_dist = (foot_pos - self.ball.data.root_pos_w[:, None, :3]).norm(dim=-1)
        nearest_foot_dist, striking_foot = self.foot_ball_dist.min(dim=1)

        if self.require_foot_contact:
            struck_this_step &= nearest_foot_dist < KICK_FOOT_CONTACT_MAX_DIST
        if self.strike_gated_return_speed:
            self.ball_return_speed = torch.where(struck_this_step | self.ball_kicked,
                                                self.ball_return_speed, torch.zeros_like(self.ball_return_speed))
        robot_ball_dist = (robot_xy - ball_xy).norm(dim=-1)
        self.kick_success_flag = (
            self.ball_active
            & (~self.ball_kicked)
            & struck_this_step
            & (robot_ball_dist < KICK_SUCCESS_MAX_DIST)
            & (self.ball_return_speed > KICK_SUCCESS_MIN_RETURN_SPEED)
        )
        if self.require_foot_contact:
            self.kick_success_flag = self.kick_success_flag & (nearest_foot_dist < KICK_FOOT_CONTACT_MAX_DIST)
        self.ball_kicked = self.ball_kicked | self.kick_success_flag

        self._update_skill(ball_xy)

        dist_from_anchor = (ball_xy - self.anchor_xy).norm(dim=-1)
        forward = torch.stack([self.anchor_yaw.cos(), self.anchor_yaw.sin()], dim=-1)
        forward_projection = ((ball_xy - self.anchor_xy) * forward).sum(dim=-1)
        ball_speed = ball_vel_xy.norm(dim=-1)
        should_end = self.ball_active & (
            (dist_from_anchor > getattr(self, "ball_end_max_distance", BALL_END_MAX_DIST_FROM_ANCHOR))
            | (forward_projection < BALL_END_MIN_FORWARD_PROJECTION)
            | (ball_speed < BALL_END_MIN_SPEED)
        )
        self.just_missed = should_end & (~self.ball_kicked)
        self.ball_active = self.ball_active & (~should_end)

        self.steps_since_ball_ended = torch.where(
            self.ball_active, torch.zeros_like(self.steps_since_ball_ended), self.steps_since_ball_ended + 1
        )
        should_reserve = (~self.ball_active) & (self.steps_since_ball_ended >= STEPS_BETWEEN_SERVES)
        reserve_ids = should_reserve.nonzero(as_tuple=False).squeeze(-1)
        self.prev_ball_vel_xy = ball_vel_xy.clone()
        if len(reserve_ids) > 0:
            self._serve(reserve_ids)


def _yaw_from_quat(quat_wxyz: torch.Tensor) -> torch.Tensor:
    w, x, y, z = quat_wxyz.unbind(-1)
    return torch.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def setup_kickball_state(
    env: ManagerBasedRLEnv,
    env_ids,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    ball_cfg: SceneEntityCfg = SceneEntityCfg("ball"),
    rsi_probability: float = RSI_PROBABILITY,
    strike_gated_return_speed: bool = False,
    require_foot_contact: bool = False,
) -> None:
    """Startup event: attach the shared state machine instance to the env.

    `rsi_probability=0.0` disables Reference State Initialization entirely, so every episode
    starts from the default stance the reset events wrote (the soccer-v2 task); the default
    keeps the v3 task's 80% mid-kick starts. `strike_gated_return_speed` restricts the ball's outward speed -- what `kick_return_task`
    pays for -- to balls that were actually struck (see `tick`). `require_foot_contact` additionally
    requires a kick to have been delivered by a foot (see `KICK_FOOT_CONTACT_MAX_DIST`).
    """
    env._kickball = KickballState(  # type: ignore[attr-defined]
        env,
        robot_cfg,
        ball_cfg,
        rsi_probability=rsi_probability,
        strike_gated_return_speed=strike_gated_return_speed,
        require_foot_contact=require_foot_contact,
    )


def reset_kickball_state(env: ManagerBasedRLEnv, env_ids: torch.Tensor) -> None:
    """Reset event: record the new anchor pose and serve the first ball for the reset envs."""
    env._kickball.reset(env_ids)  # type: ignore[attr-defined]


def tick_kickball_state(env: ManagerBasedRLEnv) -> torch.Tensor:
    """Zero-valued reward term (configured with nonzero weight): advances the state machine once per step, before every other
    reward term reads it (RewardManager evaluates terms in the order they're declared)."""
    env._kickball.tick()  # type: ignore[attr-defined]
    return torch.zeros(env.num_envs, device=env.device)
