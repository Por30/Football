#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source "${ISAAC_SIM_PATH:-/home/cao/isaacsim}/setup_conda_env.sh"
lab_root="${ISAAC_LAB_PATH:-/home/cao/IsaacLab}"
export PYTHONPATH="$lab_root/source/isaaclab:$lab_root/source/isaaclab_rl:$lab_root/source/isaaclab_tasks:$lab_root/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
output=docs/carrybox/convergence_20261014
mkdir -p "$output"
timeout --kill-after=10s 600s /home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/audit_carrybox_convergence.py --headless --enable_cameras --device cuda:0 > "$output/rollout_audit.log" 2>&1
rg -q CARRYBOX_CONVERGENCE_AUDIT_PASS "$output/rollout_audit.log"
if rg -i 'PhysX error|illegal memory access|CUDA error:|Traceback \(most recent call last\)|out of memory' "$output/rollout_audit.log"; then exit 1; fi
