"""V3 policy and stability, with a progressively narrower return-to-sender target."""
from isaaclab.managers import EventTermCfg as EventTerm, RewardTermCfg as RewTerm
from isaaclab.utils import configclass
from .agilekickball_v3_env_cfg import AgileKickballV3EnvCfg, AgileKickballV3PPORunnerCfg
from .mdp.agilekickball_v4 import (REVISION, setup_agilekickball_v4, return_to_sender_dense,
                                  return_to_sender_kick, return_to_sender_hit, return_to_sender_miss)


@configclass
class AgileKickballV4EnvCfg(AgileKickballV3EnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.events.setup_kickball_state = EventTerm(func=setup_agilekickball_v4, mode='startup',
            params={'revision': REVISION, 'initial_exposure_steps': 60000.})
        self.rewards.kick_return_task = RewTerm(func=return_to_sender_dense, weight=8.)
        self.rewards.kick_bonus = RewTerm(func=return_to_sender_kick, weight=300.)
        self.rewards.miss_penalty = RewTerm(func=return_to_sender_miss, weight=-60.)
        self.rewards.return_target_bonus = RewTerm(func=return_to_sender_hit, weight=150.)


@configclass
class AgileKickballV4PPORunnerCfg(AgileKickballV3PPORunnerCfg):
    experiment_name = 'agilekickball_v4'
