#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source "${ISAAC_SIM_PATH:-/home/cao/isaacsim}/setup_conda_env.sh"
lab_root="${ISAAC_LAB_PATH:-/home/cao/IsaacLab}"
export PYTHONPATH="$lab_root/source/isaaclab:$lab_root/source/isaaclab_rl:$lab_root/source/isaaclab_tasks:$lab_root/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out=docs/carrybox/handoff_20261014
for size in 4 4096; do
  mkdir -p "$out/scale$size"
  timeout --signal=TERM --kill-after=15s 1200s "${BALL_PYTHON:-/home/cao/ENTER/envs/ball/bin/python}" -u \
    scripts/rsl_rl/validate_carrybox_handoff.py --num-envs "$size" --output "$out/scale$size" \
    --headless --device cuda:0 > "$out/scale$size/run.log" 2>&1
  rg -q CARRYBOX_HANDOFF_PASS "$out/scale$size/run.log"
  if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/scale$size/run.log"; then exit 1; fi
done
