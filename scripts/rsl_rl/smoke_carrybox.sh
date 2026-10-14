#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
# Existing project runtime; override these two paths when using another installation.
source "${ISAAC_SIM_PATH:-/home/cao/isaacsim}/setup_conda_env.sh"
lab_root="${ISAAC_LAB_PATH:-/home/cao/IsaacLab}"
export PYTHONPATH="$lab_root/source/isaaclab:$lab_root/source/isaaclab_rl:$lab_root/source/isaaclab_tasks:$lab_root/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
mkdir -p docs/carrybox
rm -f docs/carrybox/smoke.json
"${BALL_PYTHON:-/home/cao/ENTER/envs/ball/bin/python}" -u scripts/rsl_rl/smoke_carrybox.py --headless --enable_cameras --device cuda:0 > docs/carrybox/smoke.log 2>&1
test -s docs/carrybox/smoke.json
rg -q 'CARRYBOX_SMOKE_PASS' docs/carrybox/smoke.log
