#!/usr/bin/env bash
set -euo pipefail
# Build/help only: never initialize DDS or connect to a physical robot.
MJ_ROOT="${UNITREE_MUJOCO_ROOT:-/home/cao/unitree_mujoco}"
RL_ROOT="${UNITREE_RL_LAB_ROOT:-/home/cao/unitree_rl_lab}"
cmake -S "$MJ_ROOT/simulate" -B "$MJ_ROOT/simulate/build"
cmake --build "$MJ_ROOT/simulate/build" -j2
cmake -S "$RL_ROOT/deploy/robots/g1_29dof" -B "$RL_ROOT/deploy/robots/g1_29dof/build"
cmake --build "$RL_ROOT/deploy/robots/g1_29dof/build" -j2
"$MJ_ROOT/simulate/build/unitree_mujoco" --help
"$RL_ROOT/deploy/robots/g1_29dof/build/g1_ctrl" --help
