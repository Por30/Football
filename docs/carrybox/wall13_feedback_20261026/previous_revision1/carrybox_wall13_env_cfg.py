"""Independent wall13 using the edited FindBox stationary-hold demonstrations."""
from isaaclab.utils import configclass
from perceptual_ball.carrybox_amp import DEFAULT_DATASET_PATH
from .carrybox_wall12_env_cfg import CarryBoxWalled12EnvCfg, CarryBoxWalled12PPORunnerCfg


@configclass
class CarryBoxWalled13EnvCfg(CarryBoxWalled12EnvCfg):
    walled_variant: str = 'walled13'


@configclass
class CarryBoxWalled13PPORunnerCfg(CarryBoxWalled12PPORunnerCfg):
    experiment_name = 'g1_carrybox_depth/walled13'
    run_name = 'wall13_stationary_hold_pose_aux_v1'

    def __post_init__(self):
        super().__post_init__()
        # Named revision 3: 11 locomotion + 3 pickup + 1 stationary-hold clip.
        # Wall12 already resolved to this dataset; keep its weights and RSI.
        self.algorithm.amp_data_dir = DEFAULT_DATASET_PATH
