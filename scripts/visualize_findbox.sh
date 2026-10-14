#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/.."
source "${ISAAC_SIM_PATH:-/home/cao/isaacsim}/setup_conda_env.sh"
lab_root="${ISAAC_LAB_PATH:-/home/cao/IsaacLab}"
export PYTHONPATH="$lab_root/source/isaaclab:$lab_root/source/isaaclab_rl:$lab_root/source/isaaclab_tasks:$lab_root/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
"${BALL_PYTHON:-/home/cao/ENTER/envs/ball/bin/python}" -u scripts/visualize_findbox.py --headless --enable_cameras --device cpu "$@"
