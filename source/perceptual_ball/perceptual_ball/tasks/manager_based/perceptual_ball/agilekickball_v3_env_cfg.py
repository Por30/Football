"""V2 physical task, explicit stable auxiliary settings and v2 weight initialization."""
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.utils import configclass
from isaaclab_rl.rsl_rl import RslRlPpoActorCriticCfg
from .agilekickball_env_cfg import AgileAlgorithmCfg
from .agilekickball_v2_env_cfg import AgileKickballV2EnvCfg, AgileKickballV2PPORunnerCfg
from .mdp.agilekickball_v3 import REVISION, setup_agilekickball_v3


@configclass
class AgileKickballV3EnvCfg(AgileKickballV2EnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.events.setup_kickball_state = EventTerm(
            func=setup_agilekickball_v3, mode='startup',
            params={'revision': REVISION, 'initial_exposure_steps': 60000.})


@configclass
class StableFeedbackPolicyCfg(RslRlPpoActorCriticCfg):
    feedback_logstd_min: float = -2.
    feedback_logstd_max: float = 1.
    feedback_smooth_std: bool = True
    feedback_residual_limit: float = .1


@configclass
class StableFeedbackAlgorithmCfg(AgileAlgorithmCfg):
    ball_aux_coef: float = .5
    ball_aux_lr: float = 1.e-4
    ball_aux_max_kl: float = 1.e-3
    ball_aux_update_encoder: bool = False


@configclass
class AgileKickballV3PPORunnerCfg(AgileKickballV2PPORunnerCfg):
    experiment_name = 'agilekickball_v3'
    policy = StableFeedbackPolicyCfg(**AgileKickballV2PPORunnerCfg().policy.to_dict())
    algorithm = StableFeedbackAlgorithmCfg(**{
        **AgileKickballV2PPORunnerCfg().algorithm.to_dict(), 'ball_aux_lr': 1.e-4,
        'learning_rate': 1.e-5})

    def __post_init__(self):
        self.policy.class_name = 'StateFeedbackActorCritic'
        self.algorithm.class_name = 'StateFeedbackPPO'
