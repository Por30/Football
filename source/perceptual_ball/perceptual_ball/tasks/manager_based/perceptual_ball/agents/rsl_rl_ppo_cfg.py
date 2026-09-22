# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from isaaclab.utils import configclass

from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlPpoActorCriticCfg, RslRlPpoAlgorithmCfg


@configclass
class PPORunnerCfg(RslRlOnPolicyRunnerCfg):
    # Uses perceptual_ball.rsl_rl_extensions.BallRegressionOnPolicyRunner (see scripts/rsl_rl/train.py
    # and play.py), which knows how to build the classes named below. Plain rsl-rl-lib only knows its
    # own "ActorCritic"/"PPO"/"OnPolicyRunner".
    class_name = "BallRegressionOnPolicyRunner"
    num_steps_per_env = 24
    # matches the x2_kickball_depth_v3 recipe's 50000; override with --max_iterations for a quick
    # smoke test (e.g. --max_iterations 3)
    max_iterations = 50000
    save_interval = 200
    experiment_name = "g1_soccer_kick"
    # The policy only sees an 8-frame history of proprioception + the (synthetic) depth camera --
    # it has to perceive the ball through the camera and can't see its own root velocity either;
    # the critic gets a single current-frame proprioception reading plus its true root velocity
    # and the ball's true pose/velocity as privileged info (matching the recipe's
    # actor_obs_history_length=8 / critic_obs_history_length=1 split).
    obs_groups = {
        "policy": ["proprio_hist", "perception"],
        "critic": ["proprio", "robot_vel", "privileged"],
    }
    policy = RslRlPpoActorCriticCfg(
        class_name="PerceptionActorCritic",
        init_noise_std=1.0,
        # the actor bypasses this normalizer entirely (it routes "perception" through its own CNN
        # encoder instead of a flat normalized vector); only the critic's stock MLP uses one.
        actor_obs_normalization=False,
        critic_obs_normalization=True,
        actor_hidden_dims=[512, 256, 256],
        critic_hidden_dims=[512, 256, 256],
        activation="elu",
    )
    algorithm = RslRlPpoAlgorithmCfg(
        class_name="BallRegressionPPO",
        value_loss_coef=1.0,
        use_clipped_value_loss=True,
        clip_param=0.2,
        entropy_coef=0.01,
        num_learning_epochs=5,
        num_mini_batches=4,
        learning_rate=1.0e-3,
        schedule="adaptive",
        gamma=0.99,
        lam=0.95,
        desired_kl=0.01,
        max_grad_norm=1.0,
    )


##
# Soccer v2: per-skill critics + per-skill AMP discriminators. See soccer_v2_env_cfg.py.
##


@configclass
class RslRlSkillActorCriticCfg(RslRlPpoActorCriticCfg):
    """`RslRlPpoActorCriticCfg` plus the network shape the v11 recipe specifies.

    The defaults of `PerceptionActorCritic` itself reproduce the v3 task's network, so that its
    checkpoints keep loading; everything v11 changes about the network is named here.
    """

    # one value function per skill (kick_left, kick_right)
    num_critics: int = 2
    # v11's DepthActorFrameDiff: 5x5 first kernel, ReLU, and a frame-difference input channel
    depth_conv_kernels: tuple[int, ...] = (5, 3, 3)
    depth_conv_paddings: tuple[int, ...] = (2, 1, 1)
    depth_activation: str = "relu"
    depth_use_frame_diff: bool = True
    # v11's auxiliary head: 128 -> 128 -> 6 rather than a bare linear probe
    ball_head_hidden_dim: int = 128


@configclass
class RslRlSkillAmpPpoAlgorithmCfg(RslRlPpoAlgorithmCfg):
    """`RslRlPpoAlgorithmCfg` plus the knobs `SkillAMPPPO` takes."""

    num_skills: int = 2
    skill_obs_group: str = "skill"
    # v11: reward = (amp_reward * amp_reward_scale) * amp_coef + task_reward * (1 - amp_coef),
    # so AMP's effective weight is 0.5 * 0.30 against the task reward's 0.70
    amp_coef: float = 0.30
    amp_reward_scale: float = 0.5
    amp_lr: float = 1.0e-3
    amp_trunk_weight_decay: float = 1.0e-3
    amp_head_weight_decay: float = 1.0e-1
    # v11 configures aux_loss_coef=1.0 but its multi-critic update never applies the loss (the
    # document calls this out as a bug). Here it is applied: without it nothing trains the depth
    # encoder to represent the ball, which is the whole point of the auxiliary head.
    ball_aux_coef: float = 1.0
    ball_aux_lr: float = 1.0e-3


@configclass
class SoccerV2PPORunnerCfg(PPORunnerCfg):
    seed = 42
    experiment_name = "g1_soccer_v2"

    # The skill gating is in neither list: v11 keeps the kicking side out of both networks, and
    # `SkillAMPPPO` reads the "skill" group off the rollout buffer by name instead (as it does
    # "amp"). The critic group order leaves "privileged" last, so the critic observation still
    # ends in [ball_pos_local, ball_vel_local] exactly as the recipe requires.
    obs_groups = {
        "policy": ["proprio_hist", "perception"],
        "critic": ["proprio", "robot_vel", "privileged"],
    }
    policy = RslRlSkillActorCriticCfg(
        class_name="PerceptionActorCritic",
        init_noise_std=1.0,
        actor_obs_normalization=False,
        # v11 runs with empirical_normalization=False: no running mean/var on any observation
        critic_obs_normalization=False,
        actor_hidden_dims=[512, 256, 256],
        critic_hidden_dims=[512, 256, 256],
        activation="elu",
    )
    algorithm = RslRlSkillAmpPpoAlgorithmCfg(
        class_name="SkillAMPPPO",
        value_loss_coef=1.0,
        use_clipped_value_loss=True,
        clip_param=0.2,
        entropy_coef=0.01,
        num_learning_epochs=5,
        num_mini_batches=4,
        learning_rate=1.0e-3,
        schedule="adaptive",
        gamma=0.99,
        lam=0.95,
        desired_kl=0.01,
        max_grad_norm=1.0,
        normalize_advantage_per_mini_batch=False,
    )


@configclass
class RslRlSoccerV3ActorCriticCfg(RslRlSkillActorCriticCfg):
    ball_aux_fuse_proprio: bool = True


@configclass
class SoccerV3PPORunnerCfg(SoccerV2PPORunnerCfg):
    experiment_name = "g1_soccer_v3"
    clip_actions = 10.0
    obs_groups = {
        "policy": ["proprio_hist", "perception", "target", "timing"],
        "critic": ["proprio", "robot_vel", "target", "privileged"],
    }
    policy = RslRlSoccerV3ActorCriticCfg(
        class_name="PerceptionActorCritic", init_noise_std=0.5,
        actor_obs_normalization=False, critic_obs_normalization=False,
        actor_hidden_dims=[512, 256, 256], critic_hidden_dims=[512, 256, 256], activation="elu")
