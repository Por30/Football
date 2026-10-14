"""V2 learning setup with longer serves and more lateral interception room."""
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.utils import configclass
from .agilekickball_v2_env_cfg import AgileKickballV2EnvCfg, AgileKickballV2PPORunnerCfg
from .mdp.agilekickball_v3 import REVISION, MAX_ROBOT_ANCHOR_DISTANCE, setup_agilekickball_v3


@configclass
class AgileKickballV3EnvCfg(AgileKickballV2EnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.events.setup_kickball_state = EventTerm(
            func=setup_agilekickball_v3, mode="startup", params={"revision": REVISION})
        self.terminations.walked_away.params["max_dist"] = MAX_ROBOT_ANCHOR_DISTANCE


@configclass
class AgileKickballV3PPORunnerCfg(AgileKickballV2PPORunnerCfg):
    experiment_name = "agilekickball_v3"
