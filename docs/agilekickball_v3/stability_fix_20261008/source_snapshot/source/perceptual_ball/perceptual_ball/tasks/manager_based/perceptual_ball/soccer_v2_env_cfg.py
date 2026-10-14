# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Soccer v2: the x2_kickball_depth_v11 recipe, on this repo's G1 kickball task.

The task definition itself is v3 and is inherited unchanged from `PerceptualBallEnvCfg`: the
same serve geometry, the same impulse-based any-direction kick test, the same six task reward
weights, no speed curriculum and no post-kick recovery phase. What v11 adds on top of v3, and
what this file configures, is:

1. **Default reset.** Every episode starts from the default standing pose (plus a random yaw)
   with the root's six velocity components written to zero, and Reference State Initialization
   is off. v3 starts 80% of episodes from a random frame of a reference kick; v11 does not, so
   the state distribution the policy trains on is the one it is deployed into.

2. **Depth sensor noise** (from v5): Gaussian noise of `0.02 * 3.0 m`, dropout on depth
   discontinuities, and uniform hole dropout -- see `mdp.perception.synthetic_ball_depth_image`.

3. **Proprioception scaling and noise** on the actor's history only. The critic reads the same
   quantities unscaled by noise, since it is privileged.

4. **Domain randomization**: per-robot friction, a fixed per-robot joint-calibration offset, a
   randomized trunk centre of mass, and a random push every 1-3 s.

5. **Left/right skill routing** (from v5): which of the two AMP discriminators grades a
   transition, and which of the two critics values it, is decided by an EMA of the ball's
   lateral position in the robot's frame (`mdp.kickball_state`). The label is deliberately kept
   out of the actor's observation -- the policy has to see from the depth image which side the
   ball is on, and the style reward is what teaches it to answer with the matching foot.

Two deviations from v11 are deliberate and switchable, both in `events.setup_kickball_state`:

- `require_foot_contact=True`. v11 calls any ball-velocity impulse above the threshold a kick.
  Measured on this task, a passive robot collects 50 "successful kicks" in 400 steps that way,
  every one of them with the nearest foot 0.47-1.19 m from the ball (median 0.78 m) -- the ball
  bouncing off its body. Requiring the strike to come off a foot removes all 50.
- `strike_gated_return_speed=True`. This one is what the v11 document actually specifies
  ("速度向量突变大于 kick_impulse_thresh 时，当前步的 ball_return_speed 使用...径向外向速度"),
  but the v3 code path in this repo reports the radial speed unconditionally, which pays the
  dense `kick_return_task` for an untouched ball rolling away past the robot.
"""

from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils import configclass
from isaaclab.utils.noise import UniformNoiseCfg as Unoise

from . import mdp
from .perceptual_ball_env_cfg import EventCfg, ObservationsCfg, PerceptualBallEnvCfg

# Depth noise, from the v5 spec. `depth_gaussian_std` is a fraction of the camera's far plane,
# not of each pixel's own range: 0.02 * 3.0 m = 0.06 m per pixel.
DEPTH_GAUSSIAN_STD = 0.02
DEPTH_EDGE_DROPOUT_PROB = 0.05
DEPTH_EDGE_GRAD_THRESH = 0.15
DEPTH_HOLE_DROPOUT_PROB = 0.02

# Observation scales, from the v11 proprioception layout.
ANG_VEL_SCALE = 0.25
JOINT_VEL_SCALE = 0.25
ROOT_LIN_VEL_SCALE = 2.0

# Actor proprioception noise, as raw (pre-scale) half-widths of a uniform distribution. Isaac Lab
# applies `noise` before `scale`, and v11 quotes the products, so e.g. angular velocity is
# 0.2 raw * 0.25 scale = the spec's 0.05, and joint velocity 1.5 * 0.25 = its 0.375.
ANG_VEL_NOISE = 0.2
GRAVITY_NOISE = 0.05
JOINT_POS_NOISE = 0.01
JOINT_VEL_NOISE = 1.5

# The trunk link whose centre of mass is randomized. The v11 recipe names X2's `waist_roll_link`;
# `torso_link` is this G1's equivalent trunk body (it is also the depth camera's mount).
TRUNK_BODY_NAME = "torso_link"


@configclass
class SkillCfg(ObsGroup):
    """One-hot `[kick_left, kick_right]` gating weights for the routed skill.

    Published as its own group but listed in neither `obs_groups["policy"]` nor
    `obs_groups["critic"]`: v11 keeps the kicking side out of both networks' inputs. The training
    side reads it off the rollout buffer by name, exactly as it does the `amp` group.
    """

    gating = ObsTerm(func=mdp.skill_gating_weights)

    def __post_init__(self) -> None:
        self.enable_corruption = False
        self.concatenate_terms = True


@configclass
class SoccerV2ObservationsCfg(ObservationsCfg):
    skill: SkillCfg = SkillCfg()


@configclass
class SoccerV2EventCfg(EventCfg):
    """v3's events plus v11's domain randomization.

    No published values exist for the three startup ranges below -- the v11 document names the
    quantities it randomizes but not their magnitudes, except for the joint offset -- so these
    are ordinary humanoid-locomotion defaults, and are the first thing to revisit if the
    sim-to-real gap shows up in one of them.
    """

    randomize_friction = EventTerm(
        func=mdp.randomize_rigid_body_material,
        mode="startup",
        params={
            "asset_cfg": SceneEntityCfg("robot", body_names=".*"),
            "static_friction_range": (0.6, 1.2),
            "dynamic_friction_range": (0.4, 1.0),
            "restitution_range": (0.0, 0.0),
            "num_buckets": 64,
        },
    )
    # the one magnitude v11 does give: +/-0.01 rad on every joint, drawn once per robot
    randomize_default_joint_pos = EventTerm(
        func=mdp.randomize_default_joint_pos,
        mode="startup",
        params={"offset_range": (-0.01, 0.01), "asset_cfg": SceneEntityCfg("robot")},
    )
    randomize_trunk_com = EventTerm(
        func=mdp.randomize_rigid_body_com,
        mode="startup",
        params={
            "asset_cfg": SceneEntityCfg("robot", body_names=TRUNK_BODY_NAME),
            "com_range": {"x": (-0.05, 0.05), "y": (-0.05, 0.05), "z": (-0.05, 0.05)},
        },
    )
    push_robot = EventTerm(
        func=mdp.push_by_setting_velocity,
        mode="interval",
        interval_range_s=(1.0, 3.0),
        params={"velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)}},
    )


@configclass
class SoccerV2EnvCfg(PerceptualBallEnvCfg):
    observations: SoccerV2ObservationsCfg = SoccerV2ObservationsCfg()
    events: SoccerV2EventCfg = SoccerV2EventCfg()

    def __post_init__(self) -> None:
        super().__post_init__()

        # (1) plain stance every reset, no RSI; see this module's docstring for the two
        # deliberate deviations switched on here
        self.events.setup_kickball_state.params = {
            "rsi_probability": 0.0,
            "strike_gated_return_speed": True,
            "require_foot_contact": True,
        }
        # spelled out rather than left to reset_root_state_uniform's implicit (0.0, 0.0) default,
        # since "the root starts at rest" is a property of this task, not an accident
        self.events.reset_robot_root_yaw.params["velocity_range"] = {
            "x": (0.0, 0.0),
            "y": (0.0, 0.0),
            "z": (0.0, 0.0),
            "roll": (0.0, 0.0),
            "pitch": (0.0, 0.0),
            "yaw": (0.0, 0.0),
        }

        # (2) noisy depth
        depth = self.observations.perception.depth_image
        depth.params["depth_gaussian_std"] = DEPTH_GAUSSIAN_STD
        depth.params["depth_edge_dropout_prob"] = DEPTH_EDGE_DROPOUT_PROB
        depth.params["depth_edge_grad_thresh"] = DEPTH_EDGE_GRAD_THRESH
        depth.params["depth_hole_dropout_prob"] = DEPTH_HOLE_DROPOUT_PROB

        # (3) proprioception scales on both copies (actor history and critic single frame), and
        # sensor noise on the actor's copy only -- the critic is privileged and reads clean state
        for group in (self.observations.proprio, self.observations.proprio_hist):
            group.base_ang_vel.scale = ANG_VEL_SCALE
            group.joint_vel_rel.scale = JOINT_VEL_SCALE
        self.observations.robot_vel.base_lin_vel.scale = ROOT_LIN_VEL_SCALE

        hist = self.observations.proprio_hist
        hist.enable_corruption = True
        hist.base_ang_vel.noise = Unoise(n_min=-ANG_VEL_NOISE, n_max=ANG_VEL_NOISE)
        hist.projected_gravity.noise = Unoise(n_min=-GRAVITY_NOISE, n_max=GRAVITY_NOISE)
        hist.joint_pos_rel.noise = Unoise(n_min=-JOINT_POS_NOISE, n_max=JOINT_POS_NOISE)
        hist.joint_vel_rel.noise = Unoise(n_min=-JOINT_VEL_NOISE, n_max=JOINT_VEL_NOISE)
        # end-effector positions and the previous action carry no noise in the v11 layout
