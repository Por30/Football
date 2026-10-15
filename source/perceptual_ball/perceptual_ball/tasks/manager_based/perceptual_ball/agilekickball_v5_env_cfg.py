"""Scene-depth football; v4 task/rewards and privileged critic remain unchanged."""
from pathlib import Path
import copy
from isaaclab.managers import EventTermCfg as EventTerm, ObservationTermCfg as ObsTerm, SceneEntityCfg
from isaaclab.envs.mdp import randomize_actuator_gains
from isaaclab.sensors import TiledCameraCfg
from isaaclab.utils import configclass
from perceptual_ball.kickball_randomized_camera import RandomizedKickballCameraCfg
from perceptual_ball.kickball_randomization import DEFAULT_DEPTH_RANDOMIZATION, validate_range, validate_depth_randomization
from perceptual_ball.kickball_depth import load_profile, target_intrinsics
from .agilekickball_v4_env_cfg import AgileKickballV4EnvCfg, AgileKickballV4PPORunnerCfg
from .agilekickball_v3_env_cfg import StableFeedbackPolicyCfg
from .mdp.agilekickball_v5 import REVISION, setup_agilekickball_v5, scene_depth_image, spawn_depth_ball

DEFAULT_PROFILE = str(Path(__file__).resolve().parents[6]/'docs/agilekickball_v5/camera_nominal.json')


@configclass
class AgileKickballV5EnvCfg(AgileKickballV4EnvCfg):
    camera_profile_path: str = DEFAULT_PROFILE
    camera_profile: dict = {}
    randomize_gains: bool = True
    kp_scale_range: tuple[float, float] = (0.9, 1.1)
    kd_scale_range: tuple[float, float] = (0.9, 1.1)
    randomize_depth: bool = True
    depth_randomization: dict = copy.deepcopy(DEFAULT_DEPTH_RANDOMIZATION)

    def __post_init__(self):
        super().__post_init__()
        self.configure_camera()
        self.scene.ball.spawn.func = spawn_depth_ball
        self.events.setup_kickball_state = EventTerm(func=setup_agilekickball_v5, mode='startup',
            params={'revision': REVISION, 'initial_exposure_steps': 60000.})
        self.observations.perception.depth_image = ObsTerm(func=scene_depth_image,
            history_length=8, flatten_history_dim=False)
        self.scene.lazy_sensor_update = True
        self.scene.ground.spawn.size = (2000., 2000.)

    def configure_camera(self):
        # Also called by Env.__init__: Hydra changes the path after config construction.
        if type(self.randomize_gains) is not bool or type(self.randomize_depth) is not bool:
            raise ValueError('Randomization enable flags must be boolean')
        validate_range(self.kp_scale_range, 'kp_scale_range', positive=True)
        validate_range(self.kd_scale_range, 'kd_scale_range', positive=True)
        validate_depth_randomization(self.depth_randomization)
        self.events.randomize_motor_gains = EventTerm(func=randomize_actuator_gains, mode='reset',
            params={'asset_cfg': SceneEntityCfg('robot'), 'operation': 'scale', 'distribution': 'uniform',
                'stiffness_distribution_params': self.kp_scale_range if self.randomize_gains else (1., 1.),
                'damping_distribution_params': self.kd_scale_range if self.randomize_gains else (1., 1.)})
        self.camera_profile = load_profile(self.camera_profile_path)
        p = self.camera_profile
        self.scene.depth_camera = RandomizedKickballCameraCfg(object_names=('Ball',),
            noise_enabled=self.randomize_depth, noise=copy.deepcopy(self.depth_randomization),
            width=p['width'], height=p['height'], near=p['near_m'], far=p['far_m'],
            update_period=p['update_period_s'], intrinsics=target_intrinsics(p),
            offset=TiledCameraCfg.OffsetCfg(pos=tuple(p['position_m']),
                rot=tuple(p['quaternion_wxyz_world']), convention='world'))


@configclass
class SceneDepthPolicyCfg(StableFeedbackPolicyCfg):
    feedback_scene_depth: bool = True


@configclass
class AgileKickballV5PPORunnerCfg(AgileKickballV4PPORunnerCfg):
    experiment_name = 'agilekickball_v5'
    policy = SceneDepthPolicyCfg(**AgileKickballV4PPORunnerCfg().policy.to_dict())
