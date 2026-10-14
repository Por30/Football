"""V1 rewards, recovery, perception and PPO; only the speed curriculum changes."""
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.utils import configclass
from .agilekickball_v1_env_cfg import AgileKickballV1EnvCfg, AgileKickballV1PPORunnerCfg
from .mdp.agilekickball_v2 import REVISION, setup_agilekickball_v2


@configclass
class AgileKickballV2EnvCfg(AgileKickballV1EnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.events.setup_kickball_state = EventTerm(func=setup_agilekickball_v2, mode='startup',
                                                    params={'revision': REVISION})


@configclass
class AgileKickballV2PPORunnerCfg(AgileKickballV1PPORunnerCfg):
    experiment_name = 'agilekickball_v2'
