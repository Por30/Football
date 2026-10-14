#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source "${ISAAC_SIM_PATH:-/home/cao/isaacsim}/setup_conda_env.sh"
lab_root="${ISAAC_LAB_PATH:-/home/cao/IsaacLab}"
export PYTHONPATH="$lab_root/source/isaaclab:$lab_root/source/isaaclab_rl:$lab_root/source/isaaclab_tasks:$lab_root/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
for variant in ${WALLED_VARIANTS:-3 4}; do
  output="${WALLED_OUTPUT_ROOT:-docs/carrybox/wall4_repair}/walled${variant}"
  extra=(--num-envs 4 --iterations 20)
  budget=600s
  phases=(geometry smoke)
  if [[ "${WALLED_SCALE_PREFLIGHT:-0}" == 1 ]]; then
    output="${WALLED_OUTPUT_ROOT:-docs/carrybox/wall4_repair}/scale128"
    extra=(--num-envs 128 --scale-preflight --iterations 50)
    budget=1200s
    phases=(smoke)
  fi
  mkdir -p "$output"
  for phase in "${phases[@]}"; do
    phase_args=()
    if [[ "$phase" == geometry ]]; then phase_args=(--geometry-only); fi
    rm -f "$output/$phase.json"
    timeout --signal=TERM --kill-after=15s "$budget" "${BALL_PYTHON:-/home/cao/ENTER/envs/ball/bin/python}" -u scripts/rsl_rl/smoke_carrybox_walled.py --variant "$variant" --headless --enable_cameras --device cuda:0 --output "$output" "${extra[@]}" "${phase_args[@]}" > "$output/$phase.log" 2>&1
    test -s "$output/$phase.json"
    rg -q 'CARRYBOX_WALLED_SMOKE_PASS' "$output/$phase.log"
    if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|Synchronizing GPU Narrowphase failed|fail to launch.*kernel|out of memory' "$output/$phase.log"; then
      echo "Fatal simulator output: $output/$phase.log" >&2
      exit 1
    fi
  done
done
