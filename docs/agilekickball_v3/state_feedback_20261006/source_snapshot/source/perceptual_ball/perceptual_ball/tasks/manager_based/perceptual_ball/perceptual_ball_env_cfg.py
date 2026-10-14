# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import CurriculumTermCfg as CurrTerm
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass

from . import mdp

##
# Pre-defined configs
##

from perceptual_ball.assets import G1_29DOF_CFG  # isort:skip


##
# Depth "camera" geometry, shared between the ball's own radius and the synthetic depth
# perception term (mdp.synthetic_ball_depth_image) -- see that function's docstring for why
# there is no real Camera/TiledCamera/RayCaster sensor in the scene. Values follow the
# x2_kickball_depth_v3 handoff recipe (/home/cao/perceptual_ball/kickball).
##

BALL_RADIUS = 0.11
CAMERA_WIDTH = 48
CAMERA_HEIGHT = 27
CAMERA_HISTORY_LENGTH = 8
CAMERA_NEAR = 0.1
CAMERA_FAR = 3.0
CAMERA_VERTICAL_FOV_DEG = 58.0
# mounted on torso_link at the real G1's own d435 depth-camera mount point (from the URDF's
# d435_joint: origin xyz=(0.0576, 0.0175, 0.4299), a 0.8308 rad ~= 47.6 deg downward pitch) --
# the actual hardware mount, not a guess, now that the 29-DOF asset carries this joint.
CAMERA_OFFSET_POS = (0.0576235, 0.01753, 0.42987)
CAMERA_OFFSET_QUAT = (0.2557, -0.6593, 0.6593, -0.2557)

# matches the x2_kickball_depth_v3 recipe's amp_imitation_body_names, adapted to G1: it names
# "left/right_wrist_roll_link" and "head_yaw_link" (X2 has a yaw-actuated neck; G1's head is a
# fixed link on the 29-DOF asset, so head_link is the closest equivalent)
END_EFFECTOR_BODY_NAMES = [
    "left_wrist_roll_link",
    "right_wrist_roll_link",
    "left_ankle_pitch_link",
    "right_ankle_pitch_link",
    "head_link",
]


##
# Scene definition
##


@configclass
class PerceptualBallSceneCfg(InteractiveSceneCfg):
    """Scene with a G1 humanoid and a soccer ball. Depth is synthesized (see PerceptionCfg), so
    there is no camera/ray-caster sensor to spawn."""

    # ground plane
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(100.0, 100.0)),
    )

    # robot
    robot: ArticulationCfg = G1_29DOF_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")

    # soccer ball. Actual spawn pose/velocity each episode is driven by the ball-serving state
    # machine (mdp.kickball_state), not this nominal init_state.
    ball: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Ball",
        spawn=sim_utils.SphereCfg(
            radius=BALL_RADIUS,
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.9, 0.9, 0.9)),
            physics_material=sim_utils.RigidBodyMaterialCfg(
                static_friction=0.6, dynamic_friction=0.5, restitution=0.5
            ),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                linear_damping=0.02,
                angular_damping=0.02,
                max_depenetration_velocity=5.0,
            ),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            mass_props=sim_utils.MassPropertiesCfg(mass=0.43),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(2.0, 0.0, BALL_RADIUS)),
    )

    # lights
    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(color=(0.9, 0.9, 0.9), intensity=500.0),
    )


##
# MDP settings
##


@configclass
class ActionsCfg:
    """Action specifications for the MDP."""

    joint_pos = mdp.JointPositionActionCfg(asset_name="robot", joint_names=[".*"], scale=0.25, use_default_offset=True)


@configclass
class ObservationsCfg:
    """Observation specifications for the MDP.

    Split into groups so the policy can be "blind" to the ball's true state (it only gets it
    through the synthetic depth image) and to its own root velocity (matching the
    x2_kickball_depth_v3 recipe, which withholds both from the actor), gets 8 frames of
    proprioception history where the critic only gets the current frame, and the critic gets
    everything else the actor doesn't. `agents/rsl_rl_ppo_cfg.py` recombines these groups per
    network via `obs_groups`.
    """

    @configclass
    class ProprioCfg(ObsGroup):
        """Single-frame proprioception, for the critic (critic_obs_history_length=1 in the
        recipe -- the critic doesn't need temporal context, it gets privileged state instead)."""

        base_ang_vel = ObsTerm(func=mdp.base_ang_vel)
        projected_gravity = ObsTerm(func=mdp.projected_gravity)
        joint_pos_rel = ObsTerm(func=mdp.joint_pos_rel)
        joint_vel_rel = ObsTerm(func=mdp.joint_vel_rel)
        end_effector_pos_b = ObsTerm(
            func=mdp.end_effector_pos_b,
            params={"asset_cfg": SceneEntityCfg("robot", body_names=END_EFFECTOR_BODY_NAMES, preserve_order=True)},
        )
        last_action = ObsTerm(func=mdp.last_action)

        def __post_init__(self) -> None:
            self.enable_corruption = False
            self.concatenate_terms = True

    @configclass
    class ProprioHistCfg(ProprioCfg):
        """Same terms as ProprioCfg, 8-frame history, for the actor (actor_obs_history_length=8
        in the recipe). Group-level history_length overrides every term's in this group."""

        def __post_init__(self) -> None:
            super().__post_init__()
            self.history_length = 8
            self.flatten_history_dim = True

    @configclass
    class PerceptionCfg(ObsGroup):
        """Synthetic depth "camera" observation, fed only to the actor (see
        mdp.synthetic_ball_depth_image). Kept as a (N, history, H, W) stack -- NOT flattened --
        since `PerceptionActorCritic` feeds it straight into a CNN encoder as image channels.
        """

        depth_image = ObsTerm(
            func=mdp.synthetic_ball_depth_image,
            params={
                "robot_cfg": SceneEntityCfg("robot", body_names="torso_link"),
                "ball_cfg": SceneEntityCfg("ball"),
                "width": CAMERA_WIDTH,
                "height": CAMERA_HEIGHT,
                "near": CAMERA_NEAR,
                "far": CAMERA_FAR,
                "ball_radius": BALL_RADIUS,
                "offset_pos": CAMERA_OFFSET_POS,
                "offset_quat": CAMERA_OFFSET_QUAT,
                "vertical_fov_deg": CAMERA_VERTICAL_FOV_DEG,
            },
            history_length=CAMERA_HISTORY_LENGTH,
            flatten_history_dim=False,
        )

        def __post_init__(self) -> None:
            self.enable_corruption = False
            self.concatenate_terms = True

    @configclass
    class RobotVelCfg(ObsGroup):
        """The robot's own root linear velocity. Critic-only (withheld from the actor, same as
        the x2_kickball_depth_v3 recipe -- real hardware can't observe this reliably either)."""

        base_lin_vel = ObsTerm(func=mdp.base_lin_vel)

        def __post_init__(self) -> None:
            self.enable_corruption = False
            self.concatenate_terms = True

    @configclass
    class PrivilegedCfg(ObsGroup):
        """Ball ground-truth state. Critic-only, and the auxiliary-head regression target."""

        ball_pos_b = ObsTerm(func=mdp.ball_pos_b)
        ball_lin_vel_b = ObsTerm(func=mdp.ball_lin_vel_b)

        def __post_init__(self) -> None:
            self.enable_corruption = False
            self.concatenate_terms = True

    @configclass
    class AmpCfg(ObsGroup):
        """AMP discriminator feature window (the "fake"/policy side; see mdp/amp.py). Not listed
        in any `obs_groups` entry in agents/rsl_rl_ppo_cfg.py -- `BallRegressionPPO` reads it
        directly off the rollout buffer by group name instead."""

        features = ObsTerm(
            func=mdp.amp_features,
            params={
                "asset_cfg": SceneEntityCfg("robot"),
                "ee_cfg": SceneEntityCfg("robot", body_names=END_EFFECTOR_BODY_NAMES, preserve_order=True),
                "ball_cfg": SceneEntityCfg("ball"),
            },
            history_length=mdp.AMP_WINDOW_LENGTH,
            flatten_history_dim=True,
        )

        def __post_init__(self) -> None:
            self.enable_corruption = False
            self.concatenate_terms = True

    # observation groups
    proprio: ProprioCfg = ProprioCfg()
    proprio_hist: ProprioHistCfg = ProprioHistCfg()
    perception: PerceptionCfg = PerceptionCfg()
    robot_vel: RobotVelCfg = RobotVelCfg()
    privileged: PrivilegedCfg = PrivilegedCfg()
    amp: AmpCfg = AmpCfg()


@configclass
class EventCfg:
    """Configuration for events."""

    # startup: attach the ball-serving/kick-detection state machine to the env (once)
    setup_kickball_state = EventTerm(func=mdp.setup_kickball_state, mode="startup")

    # reset: exactly the standing pose baked into G1_29DOF_CFG's init_state every time (no joint
    # noise), so every episode starts from the same normal standing posture. Root yaw is still
    # randomized below -- that's a facing direction, not a posture, and the task shouldn't only
    # learn to kick while facing one way.
    reset_robot_joints = EventTerm(
        func=mdp.reset_joints_by_offset,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "position_range": (0.0, 0.0),
            "velocity_range": (0.0, 0.0),
        },
    )
    reset_robot_root_yaw = EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "pose_range": {"yaw": (-3.14159, 3.14159)},
            "velocity_range": {},
        },
    )
    # must run after the two events above: records the post-reset pose as the new stand anchor
    # and serves the first ball
    reset_kickball_state = EventTerm(func=mdp.reset_kickball_state, mode="reset")


@configclass
class RewardsCfg:
    """Reward terms for the MDP, matching the x2_kickball_depth_v3 recipe. Every term, including one-shot pulses, is scaled by `step_dt` by the reward manager.
    """

    # (0) advance the ball-serving/kick-detection state machine once per step, before any other
    # reward term below reads it -- see mdp/kickball_state.py
    # NOTE: weight must be non-zero. RewardManager.compute() skips any term whose weight==0.0 as
    # a micro-optimization, and tick_kickball_state's real job is the side effect of the
    # env._kickball.tick() call, not its (always-zero) return value -- a weight of 0.0 here would
    # silently stop the whole state machine from ever advancing.
    kickball_tick = RewTerm(func=mdp.tick_kickball_state, weight=1.0)

    # (1) primary task terms
    stand_task = RewTerm(func=mdp.stand_task, weight=1.0, params={"target_height": 0.8})
    face_ball_task = RewTerm(func=mdp.face_ball_task, weight=0.5)
    kick_approach_task = RewTerm(func=mdp.kick_approach_task, weight=1.2)
    kick_return_task = RewTerm(func=mdp.kick_return_task, weight=4.0)
    kick_bonus = RewTerm(func=mdp.kick_bonus, weight=60.0)
    miss_penalty = RewTerm(func=mdp.miss_penalty, weight=-15.0)

    # (2) regularization, matching the recipe's exact term/weight list. `torque_limits` is
    # written using isaaclab.envs.mdp.applied_torque_limits, whose own docstring warns it only
    # works for explicit actuators (it diffs applied vs. computed torque); G1_29DOF_CFG uses
    # ImplicitActuatorCfg throughout, so this term is likely a structural no-op here -- kept
    # anyway for fidelity to the spec, since it's harmless either way.
    dof_acc = RewTerm(func=mdp.joint_acc_l2, weight=-1.0e-7)
    action_rate_l2 = RewTerm(func=mdp.action_rate_l2, weight=-0.03)
    joint_torques_l2 = RewTerm(func=mdp.joint_torques_l2, weight=-1.0e-4)
    dof_vel = RewTerm(func=mdp.joint_vel_l2, weight=-2.0e-4)
    dof_pos_limits = RewTerm(func=mdp.joint_pos_limits, weight=-5.0)
    dof_vel_limits = RewTerm(func=mdp.joint_vel_limits, weight=-1.0e-3, params={"soft_ratio": 1.0})
    torque_limits = RewTerm(func=mdp.applied_torque_limits, weight=-0.03)

    # NOTE: no AMP reward term here -- the real AMP discriminator reward is mixed in by
    # BallRegressionPPO.process_env_step at the algorithm level (matching the
    # x2_kickball_depth_v3 recipe), not as an env reward term. See mdp/amp.py and
    # rsl_rl_extensions/algorithm.py.


@configclass
class TerminationsCfg:
    """Termination terms for the MDP."""

    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    # not a real termination: raises on the first non-finite action/state instead of letting the
    # NaN spread into the policy weights and flatten the curves silently
    non_finite = DoneTerm(func=mdp.fail_on_non_finite_state)
    tipped = DoneTerm(func=mdp.roll_pitch_exceeded, params={"roll_limit": 0.5, "pitch_limit": 0.7})
    fell = DoneTerm(func=mdp.root_height_below_minimum, params={"minimum_height": 0.4})
    walked_away = DoneTerm(func=mdp.walked_away_from_anchor, params={"max_dist": 0.6})
    # the ankle_roll links sit ~0.2 m apart in stance and pass fore-aft of each other during a
    # kick, so 0.06 m only fires when the feet are genuinely driven through one another
    self_collision = DoneTerm(
        func=mdp.self_collision,
        params={"body_pairs": [("left_ankle_roll_link", "right_ankle_roll_link", 0.06)]},
    )


@configclass
class CurriculumCfg:
    """No curriculum terms: the v3 recipe this task follows is a fixed, low-speed task (the
    serve speed range 0.4-0.8 m/s and reward weights above are already tuned for that) -- see
    the handoff doc's closing note against adding v4/v5 curricula on top of it.
    """


##
# Environment configuration
##


@configclass
class PerceptualBallEnvCfg(ManagerBasedRLEnvCfg):
    # Scene settings
    # depth is synthesized analytically (no rendering), so num_envs can be as large as a
    # proprioception-only locomotion task; env_spacing is generous since the ball can be served
    # up to 2m from the robot and roams until 3m before being re-served
    scene: PerceptualBallSceneCfg = PerceptualBallSceneCfg(num_envs=4096, env_spacing=12.0)
    # Basic settings
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    events: EventCfg = EventCfg()
    # MDP settings
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    curriculum: CurriculumCfg = CurriculumCfg()

    # Post initialization
    def __post_init__(self) -> None:
        """Post initialization."""
        # general settings: 0.005s physics, 4 substeps/action -> 50Hz control, 12s / 600 steps
        self.decimation = 4
        self.episode_length_s = 12.0
        # viewer settings
        self.viewer.eye = (2.5, 2.5, 2.0)
        self.viewer.lookat = (0.8, 0.0, 0.3)
        # simulation settings
        self.sim.dt = 1 / 200
        self.sim.render_interval = self.decimation
