"""G1 depth find-and-lift task, intentionally independent of soccer/privileged AMP paths."""
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.envs import mdp
from isaaclab.managers import EventTermCfg as EventTerm, ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm, RewardTermCfg as RewTerm
from isaaclab.managers import TerminationTermCfg as DoneTerm, SceneEntityCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import TiledCameraCfg, ContactSensorCfg
from isaaclab.utils import configclass
from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlPpoActorCriticCfg, RslRlPpoAlgorithmCfg
from perceptual_ball.assets import G1_29DOF_CFG
from perceptual_ball.carrybox_amp import DEFAULT_DATASET_PATH
from .mdp import carrybox as task


@configclass
class CarryBoxSceneCfg(InteractiveSceneCfg):
    ground = AssetBaseCfg(prim_path='/World/ground', spawn=sim_utils.GroundPlaneCfg(size=(100., 100.)))
    robot: ArticulationCfg = G1_29DOF_CFG.replace(prim_path='{ENV_REGEX_NS}/Robot')
    box: RigidObjectCfg = RigidObjectCfg(
        prim_path='{ENV_REGEX_NS}/Box',
        spawn=sim_utils.CuboidCfg(size=task.BOX_SIZE, activate_contact_sensors=True,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(max_depenetration_velocity=1.),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.125),
            physics_material=sim_utils.RigidBodyMaterialCfg(static_friction=1., dynamic_friction=.8, restitution=0.),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.55, .35, .15))),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(.85, 0., .13)))
    depth_camera = TiledCameraCfg(
        prim_path='{ENV_REGEX_NS}/Robot/torso_link/CarryDepth',
        update_period=0., width=48, height=32, data_types=['distance_to_image_plane'],
        update_latest_camera_pose=True, depth_clipping_behavior='max',
        # Physical D435 position, 47.6 degree downward pitch. World convention: +X forward.
        offset=TiledCameraCfg.OffsetCfg(pos=(.0576235, .01753, .42987),
                                      rot=(.91495, 0., .40355, 0.), convention='world'),
        spawn=sim_utils.PinholeCameraCfg(focal_length=18., horizontal_aperture=30.,
                                        vertical_aperture=20., clipping_range=(.1, 3.)))
    left_box_contact = ContactSensorCfg(prim_path='{ENV_REGEX_NS}/Robot/left_rubber_hand',
        update_period=0., filter_prim_paths_expr=['{ENV_REGEX_NS}/Box'])
    right_box_contact = ContactSensorCfg(prim_path='{ENV_REGEX_NS}/Robot/right_rubber_hand',
        update_period=0., filter_prim_paths_expr=['{ENV_REGEX_NS}/Box'])
    light = AssetBaseCfg(prim_path='/World/Light', spawn=sim_utils.DomeLightCfg(intensity=500.))


@configclass
class CarryBoxObservationsCfg:
    @configclass
    class ProprioCfg(ObsGroup):
        state = ObsTerm(func=task.proprioception, history_length=4, flatten_history_dim=True)
        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    @configclass
    class DepthCfg(ObsGroup):
        image = ObsTerm(func=task.depth_image, history_length=4, flatten_history_dim=False)
        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    @configclass
    class TargetCfg(ObsGroup):
        pose = ObsTerm(func=task.box_pose_target)
        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    @configclass
    class AmpCfg(ObsGroup):
        motion = ObsTerm(func=task.amp_frame, history_length=task.AMP_WINDOW, flatten_history_dim=True)
        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    proprio: ProprioCfg = ProprioCfg()
    perception: DepthCfg = DepthCfg()
    box_pose_target: TargetCfg = TargetCfg()
    amp: AmpCfg = AmpCfg()


@configclass
class CarryBoxActionsCfg:
    joint_pos = mdp.JointPositionActionCfg(asset_name='robot', joint_names=['.*'], scale=.25, use_default_offset=True)


@configclass
class CarryBoxEventsCfg:
    reset_robot_root = EventTerm(func=mdp.reset_root_state_uniform, mode='reset',
        params={'pose_range': {}, 'velocity_range': {}, 'asset_cfg': SceneEntityCfg('robot')})
    reset_robot_joints = EventTerm(func=mdp.reset_joints_by_offset, mode='reset',
        params={'position_range': (0., 0.), 'velocity_range': (0., 0.)})
    reset_box = EventTerm(func=task.reset_box, mode='reset')


@configclass
class CarryBoxRewardsCfg:
    approach = RewTerm(func=task.approach_box, weight=1.)
    reach = RewTerm(func=task.reach_box, weight=2.)
    lift = RewTerm(func=task.lift_box, weight=6.)
    success = RewTerm(func=task.lift_success, weight=100.)  # +2 once on terminal control step
    action_rate = RewTerm(func=mdp.action_rate_l2, weight=-.02)
    joint_acc = RewTerm(func=mdp.joint_acc_l2, weight=-1.e-7)
    torques = RewTerm(func=mdp.joint_torques_l2, weight=-1.e-5)
    limits = RewTerm(func=mdp.joint_pos_limits, weight=-5.)
    fall = RewTerm(func=mdp.is_terminated_term, weight=-10., params={'term_keys': ['fell', 'tipped']})


@configclass
class CarryBoxTerminationsCfg:
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    invalid = DoneTerm(func=task.invalid_state)
    success = DoneTerm(func=task.lift_success)
    fell = DoneTerm(func=mdp.root_height_below_minimum, params={'minimum_height': .32})
    tipped = DoneTerm(func=mdp.bad_orientation, params={'limit_angle': 1.2})


@configclass
class CarryBoxEnvCfg(ManagerBasedRLEnvCfg):
    scene: CarryBoxSceneCfg = CarryBoxSceneCfg(num_envs=128, env_spacing=5., lazy_sensor_update=False)
    observations: CarryBoxObservationsCfg = CarryBoxObservationsCfg()
    actions: CarryBoxActionsCfg = CarryBoxActionsCfg()
    events: CarryBoxEventsCfg = CarryBoxEventsCfg()
    rewards: CarryBoxRewardsCfg = CarryBoxRewardsCfg()
    terminations: CarryBoxTerminationsCfg = CarryBoxTerminationsCfg()

    def __post_init__(self):
        self.decimation = 4
        self.episode_length_s = 12.
        self.sim.dt = .005
        self.sim.render_interval = self.decimation
        self.rerender_on_reset = True
        self.viewer.eye = (2.5, 2.5, 2.)
        self.viewer.lookat = (.7, 0., .5)


@configclass
class CarryBoxAlgorithmCfg(RslRlPpoAlgorithmCfg):
    pose_aux_coef: float = .5
    amp_coef: float = .25
    amp_reward_scale: float = 2.
    amp_lr: float = 1.e-4
    amp_data_dir: str = DEFAULT_DATASET_PATH


@configclass
class CarryBoxPPORunnerCfg(RslRlOnPolicyRunnerCfg):
    class_name = 'CarryBoxOnPolicyRunner'
    seed = 42
    num_steps_per_env = 24
    max_iterations = 30000
    save_interval = 200
    experiment_name = 'g1_carrybox_depth'
    clip_actions = 5.
    obs_groups = {'policy': ['proprio', 'perception'], 'critic': ['proprio', 'perception']}
    policy = RslRlPpoActorCriticCfg(class_name='CarryBoxActorCritic', init_noise_std=.5,
        noise_std_type='log', actor_obs_normalization=False, critic_obs_normalization=False,
        actor_hidden_dims=[256, 128], critic_hidden_dims=[256, 128], activation='elu')
    algorithm = CarryBoxAlgorithmCfg(class_name='CarryBoxPPO', value_loss_coef=1.,
        use_clipped_value_loss=True, clip_param=.2, entropy_coef=.005,
        num_learning_epochs=4, num_mini_batches=4, learning_rate=3.e-4,
        schedule='fixed', gamma=.99, lam=.95, desired_kl=None, max_grad_norm=1.)
