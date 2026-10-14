"""G1 migration: wall3 extends local CarryBox; wall4 extends wall3."""
import math
import isaaclab.sim as sim_utils
from isaaclab.assets import RigidObjectCfg
from isaaclab.managers import RewardTermCfg as RewTerm, TerminationTermCfg as DoneTerm
from isaaclab.utils import configclass
from .carrybox_env_cfg import CarryBoxEnvCfg, CarryBoxSceneCfg, CarryBoxPPORunnerCfg
from .mdp import carrybox_walled as task
from perceptual_ball.carrybox_camera import FabricTiledCamera
from perceptual_ball.carrybox_warp_camera import WarpDepthCameraCfg


def spawn_walled_robot(prim_path, cfg, **kwargs):
    """Stage-local workaround for Isaac Sim 4.5 GPU ConvexCore contacts.

    Replace only four shoulder collision cylinders; preserve the shared G1 USD,
    visual meshes, local transforms and the independent football spawn path.
    """
    import trimesh
    from pxr import Usd, UsdGeom, UsdPhysics

    prim = sim_utils.spawn_from_usd(prim_path, cfg, **kwargs)
    for root in sim_utils.find_matching_prims(prim_path):
        for child in list(Usd.PrimRange(root)):
            if child.IsInstance() and child.GetName() == 'collisions':
                child.SetInstanceable(False)
        count = 0
        for child in list(Usd.PrimRange(root)):
            if child.IsA(UsdGeom.Cylinder) and '/collisions/' in str(child.GetPath()):
                cylinder = UsdGeom.Cylinder(child)
                if cylinder.GetAxisAttr().Get() != 'Z':
                    raise ValueError('Unexpected G1 collision cylinder axis')
                geometry = trimesh.creation.cylinder(radius=cylinder.GetRadiusAttr().Get(),
                    height=cylinder.GetHeightAttr().Get(), sections=32)
                child.SetTypeName('Mesh')
                mesh = UsdGeom.Mesh(child)
                mesh.CreatePointsAttr().Set(geometry.vertices.tolist())
                mesh.CreateFaceVertexIndicesAttr().Set(geometry.faces.flatten().tolist())
                mesh.CreateFaceVertexCountsAttr().Set([3] * len(geometry.faces))
                mesh.CreateSubdivisionSchemeAttr().Set('none')
                UsdPhysics.MeshCollisionAPI.Apply(child).CreateApproximationAttr().Set('convexHull')
                count += 1
        if count != 4:
            raise ValueError(f'Expected four G1 shoulder collision cylinders, found {count}')
    return prim


def spawn_locked_obstacle(prim_path, cfg, **kwargs):
    """Six locked axes give a stationary, tensor-teleportable rigid collider."""
    from pxr import PhysxSchema
    spawn = sim_utils.spawn_cuboid if hasattr(cfg, 'size') else sim_utils.spawn_mesh_cylinder
    prim = spawn(prim_path, cfg, **kwargs)
    for root in sim_utils.find_matching_prims(prim_path):
        body = PhysxSchema.PhysxRigidBodyAPI(root)
        body.CreateLockedPosAxisAttr().Set(7)
        body.CreateLockedRotAxisAttr().Set(7)
    return prim


def obstacle(path, shape):
    # GPU kinematic set_transforms creates a reset sweep in Sim 4.5, whereas
    # USD-only static teleports do not update GPU collision positions. Locked
    # dynamic bodies support immediate tensor pose + zero velocity writes.
    shape.rigid_props = sim_utils.RigidBodyPropertiesCfg(disable_gravity=True, kinematic_enabled=False)
    shape.func = spawn_locked_obstacle
    return RigidObjectCfg(prim_path='{ENV_REGEX_NS}/'+path, spawn=shape,
                         init_state=RigidObjectCfg.InitialStateCfg(pos=(0., 0., -5.)))


@configclass
class WalledSceneCfg(CarryBoxSceneCfg):
    wall = obstacle('Wall', sim_utils.CuboidCfg(size=(.2, 8., 3.), rigid_props=None,
        collision_props=sim_utils.CollisionPropertiesCfg(),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.35,.4,.45))))
    cylinder0 = obstacle('Cylinder0', sim_utils.MeshCylinderCfg(radius=.15, height=1.8, rigid_props=None,
        collision_props=sim_utils.CollisionPropertiesCfg()))
    cylinder1 = obstacle('Cylinder1', sim_utils.MeshCylinderCfg(radius=.15, height=1.8, rigid_props=None,
        collision_props=sim_utils.CollisionPropertiesCfg()))
    cylinder2 = obstacle('Cylinder2', sim_utils.MeshCylinderCfg(radius=.15, height=1.8, rigid_props=None,
        collision_props=sim_utils.CollisionPropertiesCfg()))
    platform = obstacle('Platform', sim_utils.CuboidCfg(size=(.5,.5,.8), rigid_props=None,
        collision_props=sim_utils.CollisionPropertiesCfg()))


@configclass
class CarryBoxWalled3EnvCfg(CarryBoxEnvCfg):
    scene: WalledSceneCfg = WalledSceneCfg(num_envs=128, env_spacing=13., lazy_sensor_update=False,
        replicate_physics=False, filter_collisions=True)
    walled_variant: str = 'walled3'
    depth_backend: str = 'warp'
    reference_init: bool = True
    reset_skill_probabilities: tuple = (.8, .15, .05)
    search_prob: float = 0.
    # Local assumptions: amplitudes were not supplied in the X2 reproduction note.
    depth_noise_std_m: float = .01
    depth_max_delay_steps: int = 2
    depth_freeze_probability: float = .01
    depth_freeze_max_steps: int = 3
    camera_position_error_m: float = .005
    camera_rotation_error_deg: float = 2.

    def __post_init__(self):
        super().__post_init__()
        # This task renders optical depth only. Lighting/beauty reconstruction
        # must not consume the camera budget; synchronous depth stays enabled.
        self.sim.render = sim_utils.RenderCfg(rendering_mode='performance',
            enable_direct_lighting=False, enable_shadows=False,
            enable_dl_denoiser=False, antialiasing_mode='Off')
        self.scene.robot.spawn.func = spawn_walled_robot
        self.episode_length_s = 20.
        # Cover the 64x64 grid (13m spacing) including boundary environments.
        self.scene.ground.spawn.size = (2000., 2000.)
        camera = self.scene.depth_camera
        camera.class_type = FabricTiledCamera
        camera.width, camera.height, camera.update_period = 48, 27, .02
        camera.spawn.vertical_aperture = 2*camera.spawn.focal_length*math.tan(math.radians(58)/2)
        camera.spawn.horizontal_aperture = camera.spawn.vertical_aperture*48/27
        if self.depth_backend == 'warp':
            self.scene.depth_camera = WarpDepthCameraCfg(offset=camera.offset,
                focal_length=camera.spawn.focal_length,
                horizontal_aperture=camera.spawn.horizontal_aperture,
                vertical_aperture=camera.spawn.vertical_aperture)
            self.scene.lazy_sensor_update = True
        elif self.depth_backend != 'rtx':
            raise ValueError(f'Unsupported CarryBox depth backend: {self.depth_backend}')
        self.events.reset_box.func = task.reset_scene
        self.observations.perception.image.func = task.depth_image
        self.observations.box_pose_target.pose.func = task.box_pose_target
        self.terminations.success = None
        self.terminations.fell = DoneTerm(func=task.fallen)
        self.terminations.tipped = DoneTerm(func=task.tipped)
        self.rewards.success.func = task.success_pulse
        self.rewards.fall.func = task.failure_event
        # No applied-torque-limit penalty; ordinary torque L2 is inherited separately.
        self.rewards.held_hand_speed = RewTerm(func=task.held_joint_excess, weight=-2e-2,
                                             params={'acceleration': False, 'threshold': 1.})
        self.rewards.held_hand_acc = RewTerm(func=task.held_joint_excess, weight=-2e-5,
                                           params={'acceleration': True, 'threshold': 20.})
        self.rewards.waist_yaw_penalty = RewTerm(func=task.waist_yaw, weight=-.5)


@configclass
class CarryBoxWalled4EnvCfg(CarryBoxWalled3EnvCfg):
    walled_variant: str = 'walled4'
    search_prob: float = .02

    def __post_init__(self):
        super().__post_init__()
        self.rewards.search_turn = RewTerm(func=task.search_turn, weight=.5)


@configclass
class CarryBoxWalled3PPORunnerCfg(CarryBoxPPORunnerCfg):
    experiment_name = 'g1_carrybox_depth/walled3'
    run_name = 'walled3'


@configclass
class CarryBoxWalled4PPORunnerCfg(CarryBoxWalled3PPORunnerCfg):
    experiment_name = 'g1_carrybox_depth/walled4'
    run_name = 'walled4'
    max_iterations = 40000
