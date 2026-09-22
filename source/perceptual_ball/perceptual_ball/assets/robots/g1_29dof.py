# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unitree G1, 29-DOF variant (3-DOF waist, no fingers), converted from PhysHSI's own
g1_29dof.urdf (/home/cao/PhysHSI/legged_gym/resources/robots/g1/urdf/g1_29dof.urdf) via Isaac
Lab's URDF->USD converter (scripts/tools/convert_urdf.py). This is the same G1 embodiment/DOF
layout the parallel PhysHSI kickball effort trains against (see
/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/kickball_config.py), including its PD gains
below -- chosen deliberately so a future retargeted kicking dataset needs no joint-layout mapping
between the two.

Unlike isaaclab_assets.G1_MINIMAL_CFG (37 DOF: 1-DOF waist + 10 finger DOFs), this variant has no
fingers and a 3-DOF waist (yaw/roll/pitch), matching the real G1's most common configuration.
"""

import os

from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg
import isaaclab.sim as sim_utils

G1_29DOF_USD_PATH = os.path.join(os.path.dirname(__file__), "g1_29dof", "g1_29dof.usd")

G1_29DOF_CFG = ArticulationCfg(
    spawn=sim_utils.UsdFileCfg(
        usd_path=G1_29DOF_USD_PATH,
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            retain_accelerations=False,
            linear_damping=0.0,
            angular_damping=0.0,
            max_linear_velocity=1000.0,
            max_angular_velocity=1000.0,
            max_depenetration_velocity=1.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False, solver_position_iteration_count=8, solver_velocity_iteration_count=4
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.8),
        joint_pos={
            ".*_hip_pitch_joint": -0.1,
            ".*_hip_roll_joint": 0.0,
            ".*_hip_yaw_joint": 0.0,
            ".*_knee_joint": 0.3,
            ".*_ankle_pitch_joint": -0.2,
            ".*_ankle_roll_joint": 0.0,
            "waist_yaw_joint": 0.0,
            "waist_roll_joint": 0.0,
            "waist_pitch_joint": 0.0,
            "left_shoulder_pitch_joint": 0.0,
            "left_shoulder_roll_joint": 0.1,
            "right_shoulder_pitch_joint": 0.0,
            "right_shoulder_roll_joint": -0.1,
            ".*_shoulder_yaw_joint": 0.0,
            ".*_elbow_joint": 1.2,
            ".*_wrist_roll_joint": 0.0,
            ".*_wrist_pitch_joint": 0.0,
            ".*_wrist_yaw_joint": 0.0,
        },
        joint_vel={".*": 0.0},
    ),
    soft_joint_pos_limit_factor=0.9,
    # PD gains, standing pose, and armature match kickball_config.py's `class control`/`class
    # init_state` exactly (the parallel PhysHSI effort's own tuned values for this exact asset).
    actuators={
        "legs": ImplicitActuatorCfg(
            joint_names_expr=[".*_hip_yaw_joint", ".*_hip_roll_joint", ".*_hip_pitch_joint", ".*_knee_joint"],
            stiffness={".*_hip_yaw_joint": 150.0, ".*_hip_roll_joint": 150.0, ".*_hip_pitch_joint": 150.0, ".*_knee_joint": 300.0},
            damping={".*_hip_yaw_joint": 2.0, ".*_hip_roll_joint": 2.0, ".*_hip_pitch_joint": 2.0, ".*_knee_joint": 4.0},
            armature=0.01,
        ),
        "feet": ImplicitActuatorCfg(
            joint_names_expr=[".*_ankle_pitch_joint", ".*_ankle_roll_joint"],
            stiffness=40.0,
            damping=1.0,
            armature=0.01,
        ),
        "waist": ImplicitActuatorCfg(
            joint_names_expr=["waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint"],
            stiffness=300.0,
            damping=4.0,
            armature=0.01,
        ),
        "arms": ImplicitActuatorCfg(
            joint_names_expr=[
                ".*_shoulder_pitch_joint",
                ".*_shoulder_roll_joint",
                ".*_shoulder_yaw_joint",
                ".*_elbow_joint",
            ],
            stiffness={".*_shoulder_.*": 200.0, ".*_elbow_joint": 100.0},
            damping={".*_shoulder_.*": 3.0, ".*_elbow_joint": 1.0},
            armature=0.01,
        ),
        "wrists": ImplicitActuatorCfg(
            joint_names_expr=[".*_wrist_roll_joint", ".*_wrist_pitch_joint", ".*_wrist_yaw_joint"],
            stiffness=20.0,
            damping=0.5,
            armature=0.01,
        ),
    },
)
"""Configuration for the Unitree G1 Humanoid robot, 29-DOF variant."""
