"""Wall13 revision 3: stationary-hold AMP with directly appended pose feedback."""
from isaaclab.utils import configclass
from perceptual_ball.carrybox_amp import DEFAULT_DATASET_PATH
from .carrybox_wall12_env_cfg import CarryBoxWalled12EnvCfg, CarryBoxWalled12PPORunnerCfg


@configclass
class CarryBoxWalled13EnvCfg(CarryBoxWalled12EnvCfg):
    walled_variant: str = 'walled13'


@configclass
class CarryBoxWalled13PPORunnerCfg(CarryBoxWalled12PPORunnerCfg):
    class_name = 'CarryBoxWall13OnPolicyRunner'
    experiment_name = 'g1_carrybox_depth/walled13'
    run_name = 'wall13_pose_concat9_v3'

    def __post_init__(self):
        super().__post_init__()
        self.policy.class_name = 'CarryBoxWall13ActorCritic'
        self.algorithm.class_name = 'CarryBoxWall13PPO'
        # Named revision 3: 11 locomotion + 3 pickup + 1 stationary-hold clip.
        # Wall12 already resolved to this dataset; keep its weights and RSI.
        self.algorithm.amp_data_dir = DEFAULT_DATASET_PATH
