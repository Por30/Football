"""AgileKickball-v1: success-gated speed stages up to 5 m/s."""
from isaaclab.managers import CurriculumTermCfg as CurrTerm, EventTermCfg as EventTerm
from isaaclab.utils import configclass
from .agilekickball_env_cfg import AgileKickballEnvCfg, AgileKickballPPORunnerCfg
from .perceptual_ball_env_cfg import CurriculumCfg
from .mdp.agilekickball_v1 import setup_agilekickball_v1, success_course_speed


@configclass
class AgileKickballV1CurriculumCfg(CurriculumCfg):
    incoming_ball_speed = CurrTerm(func=success_course_speed)


@configclass
class AgileKickballV1EnvCfg(AgileKickballEnvCfg):
    curriculum: AgileKickballV1CurriculumCfg = AgileKickballV1CurriculumCfg()

    def __post_init__(self):
        super().__post_init__()
        self.events.setup_kickball_state = EventTerm(func=setup_agilekickball_v1, mode='startup', params={
            'success_threshold': .8, 'window_size': 4096, 'min_challenge_count': 1024,
            'required_windows': 2, 'min_stage_steps': 1000})


@configclass
class AgileKickballV1PPORunnerCfg(AgileKickballPPORunnerCfg):
    experiment_name = 'agilekickball_v1'
