"""V2: recovery-aware sampling and stable return rewards and speed-conditioned distance; v1 policy."""
from isaaclab.managers import EventTermCfg as EventTerm, TerminationTermCfg as DoneTerm, RewardTermCfg as RewTerm
from isaaclab.utils import configclass
from .agilekickball_v1_env_cfg import AgileKickballV1EnvCfg, AgileKickballV1PPORunnerCfg
from .perceptual_ball_env_cfg import RewardsCfg
from .mdp.agilekickball_v2 import (setup_agilekickball_v2, recovery_timed_out,
    active_kick_bonus, stable_return_bonus, failed_episode, stable_return_speed, stand_until_kick_window)


@configclass
class StableReturnRewardsCfg(RewardsCfg):
    joint_return_bonus = RewTerm(func=stable_return_bonus, weight=400.)
    failure_penalty = RewTerm(func=failed_episode, weight=-400.)


@configclass
class AgileKickballV2EnvCfg(AgileKickballV1EnvCfg):
    rewards: StableReturnRewardsCfg = StableReturnRewardsCfg()

    def __post_init__(self):
        super().__post_init__()
        self.events.setup_kickball_state = EventTerm(func=setup_agilekickball_v2, mode='startup')
        self.terminations.recovery_timeout = DoneTerm(func=recovery_timed_out)
        self.rewards.stand_task.func = stand_until_kick_window
        self.rewards.kick_return_task.func = stable_return_speed
        self.rewards.kick_bonus = RewTerm(func=active_kick_bonus, weight=100.)


@configclass
class AgileKickballV2PPORunnerCfg(AgileKickballV1PPORunnerCfg):
    experiment_name = 'agilekickball_v2'
