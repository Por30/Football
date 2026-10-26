# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import gymnasium as gym

# Wall11 control/learning, independent football semantics and checkpoint contract.
gym.register(
    id="Template-Perceptual-Ball-Kickball-v11",
    entry_point=f"{__name__}.mdp.kickball_v11:KickballV11Env",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.kickball_v11_env_cfg:KickballV11EnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.kickball_v11_env_cfg:KickballV11PPORunnerCfg",
    },
)

gym.register(
    id="Template-Perceptual-Ball-AgileKickball-v5",
    entry_point=f"{__name__}.mdp.agilekickball_v5:AgileKickballV5Env",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.agilekickball_v5_env_cfg:AgileKickballV5EnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agilekickball_v5_env_cfg:AgileKickballV5PPORunnerCfg",
    },
)

from . import agents

gym.register(
    id="Template-Perceptual-Ball-AgileKickball-v4",
    entry_point=f"{__name__}.soccer_env:SoccerEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.agilekickball_v4_env_cfg:AgileKickballV4EnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agilekickball_v4_env_cfg:AgileKickballV4PPORunnerCfg",
    },
)

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


gym.register(
    id="Template-Perceptual-Ball-CarryBox-v0",
    entry_point=f"{__name__}.mdp.carrybox:CarryBoxEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.carrybox_env_cfg:CarryBoxEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.carrybox_env_cfg:CarryBoxPPORunnerCfg",
    },
)


for _wall in (3, 4):
    gym.register(
        id=f"Template-Perceptual-Ball-CarryBox-Walled{_wall}-v0",
        entry_point=f"{__name__}.mdp.carrybox_walled:WalledCarryBoxEnv",
        disable_env_checker=True,
        kwargs={
            "env_cfg_entry_point": f"{__name__}.carrybox_walled_env_cfg:CarryBoxWalled{_wall}EnvCfg",
            "rsl_rl_cfg_entry_point": f"{__name__}.carrybox_walled_env_cfg:CarryBoxWalled{_wall}PPORunnerCfg",
        },
    )

gym.register(
    id="Template-Perceptual-Ball-CarryBox-Walled5-v0",
    entry_point=f"{__name__}.mdp.carrybox_wall5:Wall5CarryBoxEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.carrybox_wall5_env_cfg:CarryBoxWalled5EnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.carrybox_wall5_env_cfg:CarryBoxWalled5PPORunnerCfg",
    },
)

gym.register(
    id="Template-Perceptual-Ball-CarryBox-Walled10-v0",
    entry_point=f"{__name__}.mdp.carrybox_wall10:Wall10CarryBoxEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.carrybox_wall10_env_cfg:CarryBoxWalled10EnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.carrybox_wall10_env_cfg:CarryBoxWalled10PPORunnerCfg",
    },
)

gym.register(
    id="Template-Perceptual-Ball-CarryBox-Walled11-v0",
    entry_point=f"{__name__}.mdp.carrybox_wall11:Wall11CarryBoxEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.carrybox_wall11_env_cfg:CarryBoxWalled11EnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.carrybox_wall11_env_cfg:CarryBoxWalled11PPORunnerCfg",
    },
)
