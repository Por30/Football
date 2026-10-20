"""Wall5 AMP stage A with full-body external collisions for the G1 shell."""
from isaaclab.utils import configclass
from .carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg, CarryBoxWalled4PPORunnerCfg, spawn_walled_robot
from .mdp.carrybox_wall5 import amp_frame, tipped, critic_state, push_velocity_increment, action_bounds, reset_scene, locomotion_stability, walk_task
from .carrybox_env_cfg import CarryBoxObservationsCfg
from .mdp.carrybox_walled import failure_event
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup, ObservationTermCfg as ObsTerm
from perceptual_ball.carrybox_wall5 import GROUND_DATASET_PATH


def spawn_wall5_full_body_robot(prim_path, cfg, **kwargs):
    import isaaclab.sim as sim_utils
    from perceptual_ball.carrybox_fullbody_collision import add_full_body_collisions

    prim = spawn_walled_robot(prim_path, cfg, **kwargs)
    for root in sim_utils.find_matching_prims(prim_path):
        add_full_body_collisions(root)
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
    pose_visibility_supervision: bool = True
    reference_link_velocity: bool = True
    task_box_distance_3d: bool = True  # X2 root-to-box-centre reward gates, threshold 0.7 m
    ground_box_reset: bool = True
    held_box_reference_reset: bool = True  # hold keeps its reference box at hand height
    reference_motion_dataset: str = GROUND_DATASET_PATH
    reset_skill_probabilities: tuple = (.8, 0., .2)
    # Frames 32+ cause knee/box contact impulses; 34+ visibly intersect.
    ground_pickup_reset_frame_range: tuple = (0, 32)  # exclusive end

    def __post_init__(self):
        super().__post_init__()
        self.scene.robot.spawn.func = spawn_wall5_full_body_robot
        self.events.reset_box.func = reset_scene
        self.events.push_robot.func = push_velocity_increment
        # Unbound robot shapes inherit the simulation default; the ground has
        # its own material. Box material randomization remains independent.
        for material in (self.sim.physics_material, self.scene.ground.spawn.physics_material):
            material.static_friction = 1.
            material.dynamic_friction = 1.
            material.friction_combine_mode = 'multiply'
        self.observations.amp.motion.func = amp_frame
        self.scene.platform = None
        self.terminations.tipped.func = tipped
        self.rewards.early_failure = RewTerm(func=failure_event, weight=-50.)
        self.rewards.walk_task = RewTerm(func=walk_task, weight=1.)
        self.rewards.locomotion_stability = RewTerm(func=locomotion_stability, weight=5.)
        if self.depth_backend != 'warp':
            raise ValueError('Wall5 visible-pose supervision requires Warp nearest-hit IDs')
        self.scene.depth_camera.output_mesh_hits = True
        if self.depth_backend == 'warp':
            self.scene.depth_camera.object_names = tuple(
                name for name in self.scene.depth_camera.object_names if name != 'Platform')


@configclass
class CarryBoxWalled5PPORunnerCfg(CarryBoxWalled4PPORunnerCfg):
    class_name = 'CarryBoxWall5OnPolicyRunner'
    experiment_name = 'g1_carrybox_depth/walled5'
    run_name = 'walled5_distance3d_v18'

    def __post_init__(self):
        super().__post_init__()
        self.policy.class_name = 'CarryBoxWall5ActorCritic'
        self.obs_groups = {'policy': ['proprio', 'perception'], 'critic': ['critic_state']}
        self.policy.actor_hidden_dims = [512, 256, 256]
        self.policy.critic_hidden_dims = [512, 256, 256]
        self.policy.init_noise_std = 1.
        self.algorithm.pose_aux_coef = .1
        self.algorithm.learning_rate = 3.e-4
        self.algorithm.schedule = 'adaptive'
        self.algorithm.desired_kl = .01
        self.algorithm.entropy_coef = .01
        self.algorithm.num_learning_epochs = 5
        self.algorithm.class_name = 'CarryBoxWall5PPO'
        self.algorithm.amp_reward_scale = .5
        self.algorithm.amp_lr = 5.e-5
        self.algorithm.amp_data_dir = GROUND_DATASET_PATH
        self.algorithm.action_bound_coef = .01
        self.algorithm.max_action_std = 1.
