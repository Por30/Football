"""Scene-depth football; v4 task/rewards and privileged critic remain unchanged."""
from pathlib import Path
from isaaclab.managers import EventTermCfg as EventTerm, ObservationTermCfg as ObsTerm
from isaaclab.sensors import TiledCameraCfg
from isaaclab.utils import configclass
from perceptual_ball.carrybox_warp_camera import WarpDepthCameraCfg
from perceptual_ball.kickball_depth import load_profile, target_intrinsics
from .agilekickball_v4_env_cfg import AgileKickballV4EnvCfg, AgileKickballV4PPORunnerCfg
from .agilekickball_v3_env_cfg import StableFeedbackPolicyCfg
from .mdp.agilekickball_v5 import REVISION, setup_agilekickball_v5, scene_depth_image

DEFAULT_PROFILE = str(Path(__file__).resolve().parents[6]/'docs/agilekickball_v5/camera_nominal.json')


@configclass
class AgileKickballV5EnvCfg(AgileKickballV4EnvCfg):
    camera_profile_path: str = DEFAULT_PROFILE
    camera_profile: dict = {}

    def __post_init__(self):
        super().__post_init__()
        self.configure_camera()
        self.events.setup_kickball_state = EventTerm(func=setup_agilekickball_v5, mode='startup',
            params={'revision': REVISION, 'initial_exposure_steps': 60000.})
        self.observations.perception.depth_image = ObsTerm(func=scene_depth_image,
            history_length=8, flatten_history_dim=False)
        self.scene.lazy_sensor_update = True
        self.scene.ground.spawn.size = (2000., 2000.)

    def configure_camera(self):
        # Also called by Env.__init__: Hydra changes the path after config construction.
        self.camera_profile = load_profile(self.camera_profile_path)
        p = self.camera_profile
        self.scene.depth_camera = WarpDepthCameraCfg(object_names=('Ball',),
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
