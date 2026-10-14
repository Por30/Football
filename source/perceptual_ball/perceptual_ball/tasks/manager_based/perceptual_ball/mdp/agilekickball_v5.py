"""V4 return task with a versioned scene-depth observation contract."""
from .agilekickball_v4 import AgileKickballV4State
from ..soccer_env import SoccerEnv
from perceptual_ball.kickball_depth import clean_depth_m, depth_contract

REVISION = 'scene_depth_self_occlusion_20261014'


class AgileKickballV5State(AgileKickballV4State):
    curriculum_checkpoint_key = 'agile_v5_scene_depth_curriculum'

    def __init__(self, env, initial_exposure_steps=60000.):
        super().__init__(env, initial_exposure_steps)
        self.course_config['revision'] = REVISION
        self.course_config['depth_contract'] = depth_contract(env.cfg.camera_profile)
        env.depth_contract = self.course_config['depth_contract']

    def metrics(self):
        return {k.replace('AgileV4/', 'AgileV5/'): v for k, v in super().metrics().items()}


def setup_agilekickball_v5(env, env_ids, revision=REVISION, initial_exposure_steps=60000.):
    if revision != REVISION:
        raise ValueError('v5 source/config mismatch')
    env._kickball = AgileKickballV5State(env, initial_exposure_steps)
    print('[AgileKickball-v5] '+REVISION+'; camera='+env.cfg.camera_profile['calibration_status'], flush=True)


def scene_depth_image(env):
    camera = env.scene['depth_camera']
    return clean_depth_m(camera.data.output['distance_to_image_plane'][..., 0], camera.cfg.near, camera.cfg.far)


class AgileKickballV5Env(SoccerEnv):
    def __init__(self, cfg, **kwargs):
        cfg.configure_camera()
        super().__init__(cfg, **kwargs)

    def _reset_idx(self, env_ids):
        super()._reset_idx(env_ids)  # Preserve terminal training state before reset.
        self.sim.forward()  # Update child link kinematics after root/joint reset.
