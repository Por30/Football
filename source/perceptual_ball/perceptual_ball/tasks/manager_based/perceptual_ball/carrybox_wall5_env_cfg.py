"""x2g1differ.md stage A: isolate the P0 AMP changes from physical/PPO tuning."""
from isaaclab.utils import configclass
from .carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg, CarryBoxWalled4PPORunnerCfg
from .mdp.carrybox_wall5 import amp_frame


@configclass
class CarryBoxWalled5EnvCfg(CarryBoxWalled4EnvCfg):
    walled_variant: str = 'walled5'

    def __post_init__(self):
        super().__post_init__()
        self.observations.amp.motion.func = amp_frame


@configclass
class CarryBoxWalled5PPORunnerCfg(CarryBoxWalled4PPORunnerCfg):
    class_name = 'CarryBoxWall5OnPolicyRunner'
    experiment_name = 'g1_carrybox_depth/walled5'
    run_name = 'walled5_amp_stage_a'

    def __post_init__(self):
        super().__post_init__()
        self.algorithm.class_name = 'CarryBoxWall5PPO'
        self.algorithm.amp_reward_scale = .5
        self.algorithm.amp_lr = 5.e-5
