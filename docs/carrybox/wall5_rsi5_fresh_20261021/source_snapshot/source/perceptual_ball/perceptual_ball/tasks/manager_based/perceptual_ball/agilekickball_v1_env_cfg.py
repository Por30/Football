"""AgileKickball-v1: v0-based gradual incoming speed up to 5 m/s."""
from isaaclab.managers import CurriculumTermCfg as CurrTerm, EventTermCfg as EventTerm
from isaaclab.utils import configclass
from .agilekickball_env_cfg import AgileKickballEnvCfg, AgileKickballPPORunnerCfg
from .perceptual_ball_env_cfg import CurriculumCfg
from .mdp.agilekickball_v1 import setup_agilekickball_v1, incoming_speed_curriculum
from .mdp.rewards import stand_for_kick_task


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
        # RewardManager multiplies every term (including event pulses) by step_dt.
        # At 0.02 s, a kick pays 6.0 and a miss costs 1.2 before AMP mixing.
        self.rewards.stand_task.func = stand_for_kick_task
        self.rewards.face_ball_task.weight = 0.2
        self.rewards.kick_return_task.weight = 8.0
        self.rewards.kick_bonus.weight = 300.0
        self.rewards.miss_penalty.weight = -60.0


@configclass
class AgileKickballV1PPORunnerCfg(AgileKickballPPORunnerCfg):
    experiment_name = 'agilekickball_v1'
