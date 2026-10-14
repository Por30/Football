"""G1 Soccer v3: contact-verified directed return followed by sustained recovery."""
from isaaclab.managers import EventTermCfg as EventTerm, ObservationTermCfg as ObsTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup, RewardTermCfg as RewTerm
from isaaclab.managers import CurriculumTermCfg as CurrTerm
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass

from .soccer_v2_env_cfg import SoccerV2EnvCfg, SoccerV2ObservationsCfg
from .perceptual_ball_env_cfg import PerceptualBallSceneCfg, CurriculumCfg
from .mdp.soccer_v3 import (setup_soccer_v3, target_command, complete_return, failed_return,
                           recovery_reward, speed_curriculum)
from .mdp.depth_v3 import TimedDepth, depth_timing

# Explicit colliding links from this G1 USD. PhysX 4.5 returns an empty force
# column for Robot/.* here even though its shape is valid; named links work.
ROBOT_CONTACT_LINKS = ["pelvis_contour_link", "torso_link"] + [
    f"{side}_{part}" for side in ("left", "right") for part in (
        "hip_pitch_link", "hip_roll_link", "hip_yaw_link", "knee_link",
        "ankle_pitch_link", "ankle_roll_link", "shoulder_pitch_link",
        "shoulder_roll_link", "shoulder_yaw_link", "elbow_link",
        "wrist_roll_link", "wrist_pitch_link", "rubber_hand")]


@configclass
class SoccerV3SceneCfg(PerceptualBallSceneCfg):
    left_ball_contact = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/left_ankle_roll_link", history_length=4,
        update_period=0., filter_prim_paths_expr=["{ENV_REGEX_NS}/Ball"])
    right_ball_contact = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/right_ankle_roll_link", history_length=4,
        update_period=0., filter_prim_paths_expr=["{ENV_REGEX_NS}/Ball"])
    ball_robot_contact = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Ball", history_length=4,
        update_period=0., filter_prim_paths_expr=["{ENV_REGEX_NS}/Robot/" + name for name in ROBOT_CONTACT_LINKS])


@configclass
class TargetCfg(ObsGroup):
    direction = ObsTerm(func=target_command)

    def __post_init__(self):
        self.enable_corruption = False
        self.concatenate_terms = True


@configclass
class TimingCfg(ObsGroup):
    age_valid = ObsTerm(func=depth_timing)

    def __post_init__(self):
        self.enable_corruption = False
        self.concatenate_terms = True


@configclass
class SoccerV3ObservationsCfg(SoccerV2ObservationsCfg):
    target: TargetCfg = TargetCfg()
    timing: TimingCfg = TimingCfg()


@configclass
class SoccerV3CurriculumCfg(CurriculumCfg):
    serve_speed = CurrTerm(func=speed_curriculum)


@configclass
class SoccerV3EnvCfg(SoccerV2EnvCfg):
    scene: SoccerV3SceneCfg = SoccerV3SceneCfg(num_envs=1024, env_spacing=12., lazy_sensor_update=False)
    observations: SoccerV3ObservationsCfg = SoccerV3ObservationsCfg()
    curriculum: SoccerV3CurriculumCfg = SoccerV3CurriculumCfg()

    def __post_init__(self):
        super().__post_init__()
        self.scene.ball.spawn.activate_contact_sensors = True
        self.events.setup_kickball_state = EventTerm(func=setup_soccer_v3, mode="startup", params={
            "recovery_timeout": 3.0, "stable_duration": 0.3,
            "target_distance": 2.0, "target_half_width": 0.6, "max_serve_speed": 0.8})
        depth = self.observations.perception.depth_image
        depth.func = TimedDepth
        depth.params.update(capture_period_steps=2, max_delay_steps=2, frame_dropout=0.05,
                            body_occlusion_radius=0.06)
        # Begin with mild randomization; difficult perturbations are explicit variants.
        self.events.push_robot = None
        self.events.randomize_trunk_com.params["com_range"] = {
            axis: (-0.01, 0.01) for axis in ("x", "y", "z")}
        self.rewards.kick_bonus.weight = 10.0  # +0.2 raw at first valid contact
        self.rewards.complete_return = RewTerm(func=complete_return, weight=100.)  # +2 raw
        self.rewards.failed_return = RewTerm(func=failed_return, weight=-20.)  # -0.4 raw
        self.rewards.recovery = RewTerm(func=recovery_reward, weight=2.)
        self.rewards.miss_penalty = None  # a failed serve is charged exactly once
        # Implicit PD saturation must be measured from actual limits, not computed-applied torque.
        self.rewards.torque_limits = None
