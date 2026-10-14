"""AgileKickball v0: incoming-speed curriculum and recovery-gated continuous serves."""
from isaaclab.managers import CurriculumTermCfg as CurrTerm, EventTermCfg as EventTerm, TerminationTermCfg as DoneTerm
from isaaclab.utils import configclass
from isaaclab.managers import ObservationTermCfg as ObsTerm, ObservationGroupCfg as ObsGroup
from isaaclab_rl.rsl_rl import RslRlPpoAlgorithmCfg

from .perceptual_ball_env_cfg import PerceptualBallEnvCfg, CurriculumCfg, TerminationsCfg, ObservationsCfg
from .agents.rsl_rl_ppo_cfg import PPORunnerCfg
from .mdp.curriculums import ramp_incoming_ball_speed
from .mdp.agilekickball import setup_agilekickball, recovery_timed_out, ball_training_status, exposure_speed_curriculum


@configclass
class AgileKickballCurriculumCfg(CurriculumCfg):
    incoming_ball_speed = CurrTerm(func=exposure_speed_curriculum, params={"ramp_steps": 240_000})


@configclass
class AgileObservationsCfg(ObservationsCfg):
    @configclass
    class BallStatusCfg(ObsGroup):
        status = ObsTerm(func=ball_training_status)
        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True
    ball_status: BallStatusCfg = BallStatusCfg()



@configclass
class AgileKickballTerminationsCfg(TerminationsCfg):
    recovery_timeout = DoneTerm(func=recovery_timed_out)


@configclass
class AgileKickballEnvCfg(PerceptualBallEnvCfg):
    observations: AgileObservationsCfg = AgileObservationsCfg()
    curriculum: AgileKickballCurriculumCfg = AgileKickballCurriculumCfg()
    terminations: AgileKickballTerminationsCfg = AgileKickballTerminationsCfg()

    def __post_init__(self):
        super().__post_init__()
        self.episode_length_s = 60.0
        self.events.setup_kickball_state = EventTerm(func=setup_agilekickball, mode="startup", params={
            "stable_duration": .3, "serve_cooldown": .4, "recovery_timeout": 5.})


@configclass
class AgileAlgorithmCfg(RslRlPpoAlgorithmCfg):
    ball_aux_backtracking: bool = True
    ball_aux_epochs: int = 1
    ball_aux_lr: float = 1.e-3


@configclass
class AgileKickballPPORunnerCfg(PPORunnerCfg):
    experiment_name = "agilekickball_v0"
    algorithm = AgileAlgorithmCfg(**PPORunnerCfg().algorithm.to_dict())
