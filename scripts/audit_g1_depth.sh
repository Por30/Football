#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/.."
source "${ISAAC_SIM_PATH:-/home/cao/isaacsim}/setup_conda_env.sh"
lab_root="${ISAAC_LAB_PATH:-/home/cao/IsaacLab}"
export PYTHONPATH="$lab_root/source/isaaclab:$lab_root/source/isaaclab_rl:$lab_root/source/isaaclab_tasks:$lab_root/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
mkdir -p docs/carrybox/depth_audit
for variant in baseline walled3 walled4; do
  rm -f "docs/carrybox/depth_audit/${variant}.json"
  "${BALL_PYTHON:-/home/cao/ENTER/envs/ball/bin/python}" -u scripts/audit_g1_depth.py --variant "$variant" --headless --enable_cameras --device cuda:0 > "docs/carrybox/depth_audit/${variant}.log" 2>&1
  test -s "docs/carrybox/depth_audit/${variant}.json"
  rg -q 'G1_DEPTH_RENDER_PASS' "docs/carrybox/depth_audit/${variant}.log"
done
