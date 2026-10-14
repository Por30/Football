# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import gymnasium as gym

from . import agents

##
# Register Gym environments.
##

gym.register(
    id="Template-Perceptual-Ball-AgileKickball-v3-StateFeedback-20261006",
    entry_point=f"{__name__}.soccer_env:SoccerEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.agilekickball_v3_feedback_legacy_env_cfg:AgileKickballV3EnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agilekickball_v3_feedback_legacy_env_cfg:AgileKickballV3PPORunnerCfg",
    },
)

gym.register(
    id="Template-Perceptual-Ball-AgileKickball-v3-Outcome",
    entry_point=f"{__name__}.soccer_env:SoccerEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.agilekickball_v3_outcome_env_cfg:AgileKickballV3EnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agilekickball_v3_outcome_env_cfg:AgileKickballV3PPORunnerCfg",
    },
)

gym.register(
    id="Template-Perceptual-Ball-AgileKickball-v3",
    entry_point=f"{__name__}.soccer_env:SoccerEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.agilekickball_v3_env_cfg:AgileKickballV3EnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agilekickball_v3_env_cfg:AgileKickballV3PPORunnerCfg",
    },
)

gym.register(
    id="Template-Perceptual-Ball-AgileKickball-v2",
    entry_point=f"{__name__}.soccer_env:SoccerEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.agilekickball_v2_env_cfg:AgileKickballV2EnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agilekickball_v2_env_cfg:AgileKickballV2PPORunnerCfg",
    },
)

gym.register(
    id="Template-Perceptual-Ball-AgileKickball-v1",
    entry_point=f"{__name__}.soccer_env:SoccerEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.agilekickball_v1_env_cfg:AgileKickballV1EnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agilekickball_v1_env_cfg:AgileKickballV1PPORunnerCfg",
    },
)


gym.register(
    id="Template-Perceptual-Ball-AgileKickball-v0",
    entry_point=f"{__name__}.soccer_env:SoccerEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.agilekickball_env_cfg:AgileKickballEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agilekickball_env_cfg:AgileKickballPPORunnerCfg",
    },
)


gym.register(
    id="Template-Perceptual-Ball-v0",
    entry_point=f"{__name__}.soccer_env:SoccerEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.perceptual_ball_env_cfg:PerceptualBallEnvCfg",
        "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:PPORunnerCfg",
    },
)

gym.register(
    id="Template-Perceptual-Ball-Soccer-v2",
    entry_point=f"{__name__}.soccer_env:SoccerEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.soccer_v2_env_cfg:SoccerV2EnvCfg",
        "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:SoccerV2PPORunnerCfg",
    },
)

gym.register(
    id="Template-Perceptual-Ball-Soccer-v3",
    entry_point=f"{__name__}.soccer_env:SoccerEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.soccer_v3_env_cfg:SoccerV3EnvCfg",
        "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:SoccerV3PPORunnerCfg",
    },
)
