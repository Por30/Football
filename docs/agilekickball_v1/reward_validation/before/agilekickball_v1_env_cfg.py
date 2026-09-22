"""AgileKickball-v1: v0-based gradual incoming speed up to 5 m/s."""
from isaaclab.managers import CurriculumTermCfg as CurrTerm, EventTermCfg as EventTerm
from isaaclab.utils import configclass
from .agilekickball_env_cfg import AgileKickballEnvCfg, AgileKickballPPORunnerCfg
from .perceptual_ball_env_cfg import CurriculumCfg
from .mdp.agilekickball_v1 import setup_agilekickball_v1, incoming_speed_curriculum


@configclass
class AgileKickballV1CurriculumCfg(CurriculumCfg):
    incoming_ball_speed = CurrTerm(func=incoming_speed_curriculum)


@configclass
class AgileKickballV1EnvCfg(AgileKickballEnvCfg):
    curriculum: AgileKickballV1CurriculumCfg = AgileKickballV1CurriculumCfg()

    def __post_init__(self):
        super().__post_init__()
        self.events.setup_kickball_state = EventTerm(func=setup_agilekickball_v1, mode='startup', params={
            'extension_ramp_steps': 240_000})


@configclass
class AgileKickballV1PPORunnerCfg(AgileKickballPPORunnerCfg):
    experiment_name = 'agilekickball_v1'
