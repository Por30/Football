"""Independent wall12: wall11 with depth-to-box pose auxiliary supervision."""
from isaaclab.utils import configclass
from .carrybox_wall11_env_cfg import CarryBoxWalled11EnvCfg, CarryBoxWalled11PPORunnerCfg
from .mdp import carrybox_wall12 as task


@configclass
class CarryBoxWalled12EnvCfg(CarryBoxWalled11EnvCfg):
    walled_variant: str = 'walled12'

    def __post_init__(self):
        super().__post_init__()
        self.observations.perception.image.func = task.depth_image
        self.observations.box_pose_target.pose.func = task.box_pose_target
        self.events.reset_box.func = task.reset_scene


@configclass
class CarryBoxWalled12PPORunnerCfg(CarryBoxWalled11PPORunnerCfg):
    class_name = 'CarryBoxWall12OnPolicyRunner'
    experiment_name = 'g1_carrybox_depth/walled12'
    run_name = 'wall12_depth_pose_aux_v1'

    def __post_init__(self):
        super().__post_init__()
        self.algorithm.class_name = 'CarryBoxWall12PPO'
        self.algorithm.pose_aux_coef = 1.
