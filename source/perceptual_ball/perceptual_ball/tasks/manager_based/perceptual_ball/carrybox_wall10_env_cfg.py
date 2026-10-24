"""Independent PhysHSI -> FindBox wall10 lift-and-stay task."""
import math
import isaaclab.sim as sim
from isaaclab.actuators import IdealPDActuatorCfg
from isaaclab.envs import mdp
from isaaclab.managers import EventTermCfg as EventTerm, RewardTermCfg as RewTerm
from isaaclab.managers import TerminationTermCfg as DoneTerm, SceneEntityCfg
from isaaclab.managers import ObservationGroupCfg as ObsGroup, ObservationTermCfg as ObsTerm
from isaaclab.utils import configclass
from perceptual_ball.carrybox_amp import DEFAULT_DATASET_PATH
from perceptual_ball.carrybox_physhsi import spawn_physhsi_robot
from perceptual_ball.carrybox_warp_camera import WarpDepthCameraCfg
from .carrybox_env_cfg import CarryBoxEnvCfg, CarryBoxObservationsCfg, CarryBoxPPORunnerCfg
from .carrybox_walled_env_cfg import WalledSceneCfg
from .mdp import carrybox_wall10 as task
from .mdp.carrybox_wall5 import tipped
from .mdp.carrybox_physhsi import fallen_pelvis, fallen_head, fallen_hip, box_speed


@configclass
class Wall10ObservationsCfg(CarryBoxObservationsCfg):
    @configclass
    class CriticCfg(ObsGroup):
        state = ObsTerm(func=task.critic_state)
        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True
    critic_state: CriticCfg = CriticCfg()


@configclass
class Wall10RewardsCfg:
    dof_acc = RewTerm(func=task.policy_acceleration, weight=-1.e-7)
    action_rate = RewTerm(func=mdp.action_rate_l2, weight=-.03)
    torques = RewTerm(func=task.normalized_torque, weight=-1.e-4)
    dof_vel = RewTerm(func=mdp.joint_vel_l2, weight=-2.e-4)
    dof_pos_limits = RewTerm(func=mdp.joint_pos_limits, weight=-5.)
    dof_vel_limits = RewTerm(func=task.velocity_limits, weight=-1.e-3)
    torque_limits = RewTerm(func=task.torque_limits, weight=-.03)
    walk_task = RewTerm(func=task.task_reward, weight=1., params={'name': 'walk_task'})
    carryup_task = RewTerm(func=task.task_reward, weight=1., params={'name': 'carryup_task'})
    standup_task = RewTerm(func=task.task_reward, weight=.2, params={'name': 'standup_task'})


@configclass
class CarryBoxWalled10EnvCfg(CarryBoxEnvCfg):
    scene: WalledSceneCfg = WalledSceneCfg(num_envs=4096, env_spacing=10., replicate_physics=False,
                                          filter_collisions=True, lazy_sensor_update=True)
    observations: Wall10ObservationsCfg = Wall10ObservationsCfg()
    rewards: Wall10RewardsCfg = Wall10RewardsCfg()
    walled_variant: str = 'walled10'
    reference_motion_dataset: str = DEFAULT_DATASET_PATH
    hold_duration_s: float = 2.
    proprio_noise: bool = True

    def __post_init__(self):
        super().__post_init__()
        self.episode_length_s = 20.
        self.sim.render = sim.RenderCfg(rendering_mode='performance', enable_direct_lighting=False,
                                       enable_shadows=False, enable_dl_denoiser=False, antialiasing_mode='Off')
        self.scene.ground.spawn.size = (2000., 2000.)
        self.scene.ground.spawn.physics_material.static_friction = .9
        self.scene.ground.spawn.physics_material.dynamic_friction = .9
        self.scene.platform.spawn.size = (.4, .4, .02)
        self.scene.robot.spawn.func = spawn_physhsi_robot
        self.scene.robot.spawn.articulation_props.enabled_self_collisions = True
        self.scene.robot.spawn.articulation_props.solver_velocity_iteration_count = 0
        self.scene.robot.spawn.rigid_props.angular_damping = .01
        self.scene.robot.spawn.rigid_props.linear_damping = .01
        for key, old in list(self.scene.robot.actuators.items()):
            self.scene.robot.actuators[key] = IdealPDActuatorCfg(class_type=task.Wall10Actuator,
                joint_names_expr=old.joint_names_expr, stiffness=old.stiffness, damping=old.damping, armature=.01)
        self.actions.joint_pos.class_type = task.Wall10JointPositionAction
        self.scene.box.spawn.func = task.spawn_box
        self.scene.box.spawn.physics_material.static_friction = 1.
        self.scene.box.spawn.physics_material.dynamic_friction = 1.
        self.scene.box.spawn.rigid_props.angular_damping = .01
        self.scene.box.spawn.rigid_props.linear_damping = .01
        for name in ('cylinder0', 'cylinder1', 'cylinder2', 'body_contacts'):
            setattr(self.scene, name, None)
        original = self.scene.depth_camera
        vertical = 2 * 18. * math.tan(math.radians(58.) / 2)
        self.scene.depth_camera = WarpDepthCameraCfg(class_type=task.Wall10DepthCamera,
            offset=original.offset, focal_length=18., vertical_aperture=vertical,
            horizontal_aperture=vertical * 48 / 27, object_names=('Wall', 'Platform'))
        self.observations.proprio.state.func = task.proprioception
        self.observations.proprio.state.history_length = 6
        self.observations.perception.image.func = task.depth_image
        self.observations.amp.motion.func = task.amp_frame
        self.events.reset_robot_root = None
        self.events.reset_robot_joints = None
        self.events.reset_box.func = task.reset_scene
        # These match effective source startup randomization. Its declared
        # torso payload is overwritten by link_mass in the original code.
        self.events.robot_material = EventTerm(func=task.robot_material, mode='startup')
        self.events.link_mass = EventTerm(func=mdp.randomize_rigid_body_mass, mode='startup',
            params={'asset_cfg': SceneEntityCfg('robot'), 'mass_distribution_params': (.8, 1.2),
                    'operation': 'scale', 'recompute_inertia': True})
        self.events.torso_com = EventTerm(func=mdp.randomize_rigid_body_com, mode='startup',
            params={'asset_cfg': SceneEntityCfg('robot', body_names=['torso_link']),
                    'com_range': {'x': (-.1, .1), 'y': (-.1, .1), 'z': (-.1, .1)}})
        self.terminations.success = None
        self.terminations.fell = None
        self.terminations.tipped = DoneTerm(func=tipped)
        self.terminations.fell_pelvis = DoneTerm(func=fallen_pelvis)
        self.terminations.fell_head = DoneTerm(func=fallen_head)
        self.terminations.fell_hip = DoneTerm(func=fallen_hip)
        self.terminations.box_speed = DoneTerm(func=box_speed)


@configclass
class CarryBoxWalled10PPORunnerCfg(CarryBoxPPORunnerCfg):
    class_name = 'CarryBoxWall10OnPolicyRunner'
    experiment_name = 'g1_carrybox_depth/walled10'
    run_name = 'wall10_physhsi_lift_hold_v1'
    num_steps_per_env = 100
    max_iterations = 20000
    save_interval = 500
    clip_actions = 100.
    obs_groups = {'policy': ['proprio', 'perception'], 'critic': ['critic_state']}

    def __post_init__(self):
        self.policy.class_name = 'CarryBoxWall10ActorCritic'
        self.policy.actor_hidden_dims = [512, 256, 256]
        self.policy.critic_hidden_dims = [512, 256, 256]
        self.policy.init_noise_std = 1.
        self.algorithm.class_name = 'CarryBoxWall10PPO'
        self.algorithm.pose_aux_coef = 0.  # PhysHSI has no auxiliary pose objective.
        self.algorithm.learning_rate = 1.e-3
        self.algorithm.amp_lr = 1.e-3
        self.algorithm.amp_reward_scale = .5
        self.algorithm.schedule = 'adaptive'
        self.algorithm.desired_kl = .01
        self.algorithm.entropy_coef = .01
        self.algorithm.num_learning_epochs = 5
        self.algorithm.num_mini_batches = 4
