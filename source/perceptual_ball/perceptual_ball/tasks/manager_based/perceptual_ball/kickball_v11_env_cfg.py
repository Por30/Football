"""Kickball v11: wall11 learning/control, no walls, continuous five-m/s returns."""
from isaaclab.managers import (EventTermCfg as EventTerm, RewardTermCfg as RewTerm,
    ObservationTermCfg as ObsTerm, ObservationGroupCfg as ObsGroup,
    TerminationTermCfg as DoneTerm, CurriculumTermCfg as CurrTerm)
from isaaclab.utils import configclass
from perceptual_ball.carrybox_warp_camera import WarpDepthCamera
from perceptual_ball.kickball_v11 import MOTION_DIR
from .carrybox_wall11_env_cfg import CarryBoxWalled11EnvCfg, CarryBoxWalled11PPORunnerCfg
from .carrybox_wall10_env_cfg import Wall10ObservationsCfg, Wall10RewardsCfg
from .perceptual_ball_env_cfg import PerceptualBallSceneCfg
from .mdp import kickball_v11 as task
from .mdp import agilekickball_v4 as returns
from .mdp.kickball_state import tick_kickball_state
from .mdp.agilekickball import recovery_timed_out
from .mdp.rewards import stand_for_kick_task, face_ball_task, kick_approach_task
from .mdp.terminations import fail_on_non_finite_state, walked_away_from_anchor
from .mdp.agilekickball_v5 import spawn_depth_ball


@configclass
class KickballObservationsCfg(Wall10ObservationsCfg):
    @configclass
    class BallTargetCfg(ObsGroup):
        state = ObsTerm(func=task.ball_target)
        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True
    ball_target: BallTargetCfg = BallTargetCfg()
    box_pose_target = None


@configclass
class KickballRewardsCfg(Wall10RewardsCfg):
    walk_task = None
    carryup_task = None
    standup_task = None
    kickball_tick = RewTerm(func=tick_kickball_state, weight=1.)
    stand_task = RewTerm(func=stand_for_kick_task, weight=1., params={'target_height': .8})
    face_ball_task = RewTerm(func=face_ball_task, weight=.2)
    kick_approach_task = RewTerm(func=kick_approach_task, weight=1.2)
    kick_return_task = RewTerm(func=returns.return_to_sender_dense, weight=8.)
    kick_bonus = RewTerm(func=returns.return_to_sender_kick, weight=300.)
    miss_penalty = RewTerm(func=returns.return_to_sender_miss, weight=-60.)
    return_target_bonus = RewTerm(func=returns.return_to_sender_hit, weight=150.)


@configclass
class KickballCurriculumCfg:
    incoming_speed = CurrTerm(func=task.curriculum)


@configclass
class KickballV11EnvCfg(CarryBoxWalled11EnvCfg):
    observations: KickballObservationsCfg = KickballObservationsCfg()
    rewards: KickballRewardsCfg = KickballRewardsCfg()
    curriculum: KickballCurriculumCfg = KickballCurriculumCfg()
    reference_motion_dataset: str = MOTION_DIR
    walled_variant: str = 'kickballv11'

    def __post_init__(self):
        super().__post_init__()
        for name in ('box', 'wall', 'platform', 'cylinder0', 'cylinder1', 'cylinder2',
                     'left_box_contact', 'right_box_contact'):
            setattr(self.scene, name, None)
        self.scene.ball = PerceptualBallSceneCfg().ball.copy()
        self.scene.ball.spawn.func = spawn_depth_ball
        self.scene.depth_camera.class_type = WarpDepthCamera
        self.scene.depth_camera.object_names = ('Ball',)
        self.observations.critic_state.state.func = task.critic_state
        self.observations.amp.motion.func = task.amp_frame
        self.events.reset_box = None
        self.events.setup_kickball_state = EventTerm(func=task.setup, mode='startup')
        self.events.reset_kickball = EventTerm(func=task.reset_scene, mode='reset')
        self.terminations.invalid = DoneTerm(func=fail_on_non_finite_state)
        self.terminations.box_speed = None
        self.terminations.recovery_timeout = DoneTerm(func=recovery_timed_out)
        self.terminations.walked_away = DoneTerm(func=walked_away_from_anchor, params={'max_dist': .6})


@configclass
class KickballV11PPORunnerCfg(CarryBoxWalled11PPORunnerCfg):
    class_name = 'KickballV11OnPolicyRunner'
    experiment_name = 'agilekickball_v4/kickballv11'
    run_name = 'wall11_return5_aux_standing'

    def __post_init__(self):
        super().__post_init__()
        self.policy.class_name = 'KickballV11ActorCritic'
        self.algorithm.class_name = 'KickballV11PPO'
        self.algorithm.pose_aux_coef = 1.
        self.algorithm.amp_data_dir = MOTION_DIR
