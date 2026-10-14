#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source "${ISAAC_SIM_PATH:-/home/cao/isaacsim}/setup_conda_env.sh"
lab_root="${ISAAC_LAB_PATH:-/home/cao/IsaacLab}"
export PYTHONPATH="$lab_root/source/isaaclab:$lab_root/source/isaaclab_rl:$lab_root/source/isaaclab_tasks:$lab_root/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out=docs/carrybox/warp_20261014
for phase in compare4 geometry scale4096; do
  mkdir -p "$out/$phase"
  script=scripts/rsl_rl/benchmark_carrybox_warp.py
  size=4
  extra=(--enable_cameras)
  marker=CARRYBOX_WARP_PASS
  if [[ "$phase" == geometry ]]; then
    script=scripts/rsl_rl/smoke_carrybox_walled.py
    extra=(--variant 4 --geometry-only)
    marker=CARRYBOX_WALLED_SMOKE_PASS
  elif [[ "$phase" == scale4096 ]]; then size=4096; extra=(); fi
  timeout --signal=TERM --kill-after=15s 1200s /home/cao/ENTER/envs/ball/bin/python -u "$script" \
    --num-envs "$size" --output "$out/$phase" --headless --device cuda:0 "${extra[@]}" > "$out/$phase/run.log" 2>&1
  rg -q "$marker" "$out/$phase/run.log"
  if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/$phase/run.log"; then exit 1; fi
done
