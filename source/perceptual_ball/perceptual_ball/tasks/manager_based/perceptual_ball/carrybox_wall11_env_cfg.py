"""Independent wall11: wall10 learning/control with noisy depth and obstacles."""
from isaaclab.utils import configclass
from perceptual_ball.carrybox_wall11 import DEPTH_NOISE
from .carrybox_wall10_env_cfg import CarryBoxWalled10EnvCfg, CarryBoxWalled10PPORunnerCfg
from .carrybox_walled_env_cfg import WalledSceneCfg
from .mdp import carrybox_wall11 as task


@configclass
class CarryBoxWalled11EnvCfg(CarryBoxWalled10EnvCfg):
    walled_variant: str = 'walled11'
    depth_noise: dict = DEPTH_NOISE.copy()

    def __post_init__(self):
        super().__post_init__()
        obstacles = WalledSceneCfg()
        for name in ('cylinder0', 'cylinder1', 'cylinder2'):
            setattr(self.scene, name, getattr(obstacles, name).copy())
        self.scene.depth_camera.object_names = ('Wall', 'Platform', 'Cylinder0', 'Cylinder1', 'Cylinder2')
        self.observations.perception.image.func = task.depth_image
        self.events.reset_box.func = task.reset_scene


@configclass
class CarryBoxWalled11PPORunnerCfg(CarryBoxWalled10PPORunnerCfg):
    experiment_name = 'g1_carrybox_depth/walled11'
    run_name = 'wall11_noisy_depth_obstacles_v1'
    num_steps_per_env = 24
