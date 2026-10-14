"""State-feedback v3: same environment/observations/rewards as v2."""
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.utils import configclass
from .agilekickball_v2_env_cfg import AgileKickballV2EnvCfg, AgileKickballV2PPORunnerCfg
from .mdp.agilekickball_v3 import REVISION, setup_agilekickball_v3


@configclass
class AgileKickballV3EnvCfg(AgileKickballV2EnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.events.setup_kickball_state = EventTerm(
            func=setup_agilekickball_v3, mode='startup', params={'revision': REVISION})


@configclass
class AgileKickballV3PPORunnerCfg(AgileKickballV2PPORunnerCfg):
    experiment_name = 'agilekickball_v3'

    def __post_init__(self):
        self.policy.class_name = 'StateFeedbackActorCritic'
        self.algorithm.class_name = 'StateFeedbackPPO'
