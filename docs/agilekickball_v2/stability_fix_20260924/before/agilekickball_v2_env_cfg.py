"""V2: recovery-aware sampling and continuous stability windows; v1 policy/rewards."""
from isaaclab.managers import EventTermCfg as EventTerm, TerminationTermCfg as DoneTerm
from isaaclab.utils import configclass
from .agilekickball_v1_env_cfg import AgileKickballV1EnvCfg, AgileKickballV1PPORunnerCfg
from .mdp.agilekickball_v2 import setup_agilekickball_v2, recovery_timed_out


@configclass
class AgileKickballV2EnvCfg(AgileKickballV1EnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.events.setup_kickball_state = EventTerm(func=setup_agilekickball_v2, mode='startup')
        self.terminations.recovery_timeout = DoneTerm(func=recovery_timed_out)


@configclass
class AgileKickballV2PPORunnerCfg(AgileKickballV1PPORunnerCfg):
    experiment_name = 'agilekickball_v2'
