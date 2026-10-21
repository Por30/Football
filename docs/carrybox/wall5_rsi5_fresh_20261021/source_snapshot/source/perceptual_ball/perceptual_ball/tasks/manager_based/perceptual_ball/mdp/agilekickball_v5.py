"""V4 return task with a versioned scene-depth observation contract."""
from .agilekickball_v4 import AgileKickballV4State
from ..soccer_env import SoccerEnv
from perceptual_ball.kickball_depth import clean_depth_m, depth_contract
import isaaclab.sim as sim_utils
import copy

REVISION = 'scene_depth_gain_noise_20261014'


@sim_utils.clone
def spawn_depth_ball(prim_path, cfg, translation=None, orientation=None, **kwargs):
    """Explicit visual triangles; keep the original ideal sphere collider unchanged.

    USD's implicit Sphere is tessellated differently by different renderers.
    Author one visible surface so Warp, RTX and saved scene geometry agree.
    """
    import trimesh
    from pxr import UsdGeom, UsdShade
    root = sim_utils.spawn_sphere(prim_path, cfg, translation, orientation, **kwargs)
    stage = root.GetStage()
    collider = stage.GetPrimAtPath(prim_path+'/geometry/mesh')
    material, _ = UsdShade.MaterialBindingAPI(collider).ComputeBoundMaterial()
    UsdGeom.Imageable(collider).MakeInvisible()
    geometry = trimesh.creation.uv_sphere(radius=cfg.radius, count=[64, 64])
    visual = UsdGeom.Mesh.Define(stage, prim_path+'/geometry/depth_visual')
    visual.CreatePointsAttr().Set(geometry.vertices.tolist())
    visual.CreateFaceVertexCountsAttr().Set([3]*len(geometry.faces))
    visual.CreateFaceVertexIndicesAttr().Set(geometry.faces.flatten().tolist())
    visual.CreateSubdivisionSchemeAttr().Set('none')
    visual.CreateDoubleSidedAttr().Set(True)
    if material:
        UsdShade.MaterialBindingAPI.Apply(visual.GetPrim()).Bind(material)
    return root


class AgileKickballV5State(AgileKickballV4State):
    curriculum_checkpoint_key = 'agile_v5_scene_depth_curriculum'

    def __init__(self, env, initial_exposure_steps=60000.):
        super().__init__(env, initial_exposure_steps)
        self.course_config['revision'] = REVISION
        self.course_config['depth_contract'] = depth_contract(env.cfg.camera_profile)
        env.depth_contract = self.course_config['depth_contract']
        robot=env.scene['robot']
        env.depth_contract['training_randomization'] = {
            'schema': 1, 'training_only': True,
            'gains': {'enabled': env.cfg.randomize_gains,
                'kp_scale_range': list(env.cfg.kp_scale_range), 'kd_scale_range': list(env.cfg.kd_scale_range),
                'sampling': 'independent_per_joint_per_environment_per_reset_from_nominal',
                'joint_names': list(robot.joint_names),
                'nominal_kp': robot.data.default_joint_stiffness[0].cpu().tolist(),
                'nominal_kd': robot.data.default_joint_damping[0].cpu().tolist()},
            'depth': {'enabled': env.cfg.randomize_depth, 'ranges': copy.deepcopy(env.cfg.depth_randomization),
                'parameters': 'per_environment_per_reset', 'noise': 'once_per_sensor_capture',
                'sigma_m': 'sigma_m + sigma_distance * optical_z_m**2',
                'miss_and_hole': 'far=3m', 'geometry': 'noise_after_nearest_surface_no_background_reveal'},
        }

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
