"""Wall5 revision28: clean depth and a gentler early push curriculum."""
from isaaclab.utils import configclass
from isaaclab.envs.mdp import is_alive
from .carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg, CarryBoxWalled4PPORunnerCfg, spawn_walled_robot
from .mdp.carrybox_wall5 import amp_frame, tipped, critic_state, push_velocity_increment, action_bounds, reset_scene, walk_task, grasp_task_reward
from .carrybox_env_cfg import CarryBoxObservationsCfg
from .mdp.carrybox_physhsi import (reset_scene, PhysHSIJointPositionAction,
    fallen_pelvis, fallen_head, fallen_hip, box_speed)
from perceptual_ball.carrybox_physhsi import spawn_physhsi_robot, RSI_SKILL_PROBABILITIES, RESET_PROFILE
from isaaclab.managers import RewardTermCfg as RewTerm, TerminationTermCfg as DoneTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup, ObservationTermCfg as ObsTerm
from perceptual_ball.carrybox_wall5 import GROUND_DATASET_PATH, AMP_DATASET_PATH, grasp_reward_geometry
from perceptual_ball.carrybox_reward_geometry import g1_reward_geometry


def spawn_wall5_full_body_robot(prim_path, cfg, **kwargs):
    import isaaclab.sim as sim_utils
    from perceptual_ball.carrybox_fullbody_collision import add_full_body_collisions, configure_wall5_self_collision

    prim = spawn_walled_robot(prim_path, cfg, **kwargs)
    for root in sim_utils.find_matching_prims(prim_path):
        add_full_body_collisions(root)
        if cfg.articulation_props.enabled_self_collisions:
            configure_wall5_self_collision(root)
    return prim


@configclass
class Wall5ObservationsCfg(CarryBoxObservationsCfg):
    @configclass
    class CriticCfg(ObsGroup):
        state = ObsTerm(func=critic_state)

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    critic_state: CriticCfg = CriticCfg()

    @configclass
    class ActionBoundsCfg(ObsGroup):
        bounds = ObsTerm(func=action_bounds)
        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    action_bounds: ActionBoundsCfg = ActionBoundsCfg()


@configclass
class CarryBoxWalled5EnvCfg(CarryBoxWalled4EnvCfg):
    observations: Wall5ObservationsCfg = Wall5ObservationsCfg()
    walled_variant: str = 'walled5'
    # Keep the paired visibility flag for diagnostics; revision22 supervises all frames.
    pose_visibility_supervision: bool = True
    depth_in_metres: bool = True
    # Clean optical depth for this training stage; geometric occlusion remains.
    depth_noise_std_m: float = 0.
    depth_stereo_near_m: float = 0.
    depth_stereo_far_m: float = 0.
    depth_edge_probability: float = 0.
    depth_hole_probability: float = 0.
    depth_max_delay_steps: int = 0
    depth_delay_probability: float = 0.
    depth_freeze_probability: float = 0.
    depth_freeze_max_steps: int = 1
    camera_position_error_m: float = 0.
    camera_rotation_error_deg: float = 0.
    # Preserve additive pushes and final amplitude; defer and slow their onset.
    push_warmup_iterations: int = 5000
    push_ramp_iterations: int = 10000
    reference_link_velocity: bool = True
    task_box_distance_3d: bool = True
    reward_geometry: dict = dict(g1_reward_geometry(), near_distance=.90, profile='g1_grasp_geometry_v23')
    grasp_geometry: dict = grasp_reward_geometry()
    height_termination_terms: tuple = ('fell_pelvis', 'fell_head', 'fell_hip')
    robot_reset_profile: str = RESET_PROFILE
    ground_box_reset: bool = False
    held_box_reference_reset: bool = True  # hold keeps its reference box at hand height
    reference_motion_dataset: str = AMP_DATASET_PATH
    reset_skill_probabilities: tuple = RSI_SKILL_PROBABILITIES  # conditional on 80% reference branch
    reset_reference_probability: float = .8
    # Legacy field is unused by the continuous PhysHSI initializer.
    ground_pickup_reset_frame_range: tuple = (0, 32)  # exclusive end

    def __post_init__(self):
        super().__post_init__()
        self.scene.robot.spawn.func = spawn_physhsi_robot
        self.actions.joint_pos.class_type = PhysHSIJointPositionAction
        self.events.default_joint_pos.params = {'magnitude': 0.}
        self.scene.robot.spawn.articulation_props.enabled_self_collisions = True
        self.events.reset_box.func = reset_scene
        self.events.push_robot.func = push_velocity_increment
        # Unbound robot shapes inherit the simulation default; the ground has
        # its own material. Box material randomization remains independent.
        for material in (self.sim.physics_material, self.scene.ground.spawn.physics_material):
            material.static_friction = 1.
            material.dynamic_friction = 1.
            material.friction_combine_mode = 'multiply'
        self.observations.amp.motion.func = amp_frame
        # Match local PhysHSI: abs(roll)>0.5 or abs(pitch)>1.1 radians.
        self.terminations.tipped = DoneTerm(func=tipped)
        self.terminations.fell = None
        self.terminations.fell_pelvis = DoneTerm(func=fallen_pelvis)
        self.terminations.fell_head = DoneTerm(func=fallen_head)
        self.terminations.fell_hip = DoneTerm(func=fallen_hip)
        self.terminations.box_speed = DoneTerm(func=box_speed)
        self.rewards.undesired_contacts = None
        self.rewards.early_failure = None
        # +0.06 per valid 50 Hz transition. No posture target: reaching/squatting
        # remains possible under the existing physical termination thresholds.
        self.rewards.alive = RewTerm(func=is_alive, weight=3.)
        self.rewards.walk_task = RewTerm(func=walk_task, weight=1.)
        for name in ('carryup_task', 'stable_grasp', 'slow_pickup', 'arm_speed_pickup', 'arm_acc_pickup'):
            getattr(self.rewards, name).func = grasp_task_reward
        if self.depth_backend != 'warp':
            raise ValueError('Wall5 visible-pose supervision requires Warp nearest-hit IDs')
        self.scene.depth_camera.output_mesh_hits = True


@configclass
class CarryBoxWalled5PPORunnerCfg(CarryBoxWalled4PPORunnerCfg):
    class_name = 'CarryBoxWall5OnPolicyRunner'
    experiment_name = 'g1_carrybox_depth/walled5'
    run_name = 'walled5_clean_depth_gentle_push_v28'

    def __post_init__(self):
        super().__post_init__()
        self.policy.class_name = 'CarryBoxWall5ActorCritic'
        self.obs_groups = {'policy': ['proprio', 'perception'], 'critic': ['critic_state']}
        self.policy.actor_hidden_dims = [512, 256, 256]
        self.policy.critic_hidden_dims = [512, 256, 256]
        self.policy.init_noise_std = 1.
        self.algorithm.pose_aux_coef = 1.0
        self.algorithm.learning_rate = 3.e-4
        self.algorithm.schedule = 'adaptive'
        self.algorithm.desired_kl = .01
        self.algorithm.entropy_coef = .01
        self.algorithm.num_learning_epochs = 5
        self.algorithm.class_name = 'CarryBoxWall5PPO'
        self.algorithm.amp_reward_scale = .5
        self.algorithm.amp_lr = 5.e-5
        self.algorithm.amp_data_dir = AMP_DATASET_PATH
        self.algorithm.action_bound_coef = .01
        self.algorithm.max_action_std = 1.
