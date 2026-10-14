#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source "${ISAAC_SIM_PATH:-/home/cao/isaacsim}/setup_conda_env.sh"
lab_root="${ISAAC_LAB_PATH:-/home/cao/IsaacLab}"
export PYTHONPATH="$lab_root/source/isaaclab:$lab_root/source/isaaclab_rl:$lab_root/source/isaaclab_tasks:$lab_root/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
output=docs/carrybox/performance_20261014
mkdir -p "$output/geometry" "$output/pose4" "$output/scale4096"
for size in 4 4096; do
  target="$output/pose4"
  if [[ "$size" == 4096 ]]; then target="$output/scale4096"; fi
  timeout --signal=TERM --kill-after=15s 1000s /home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/benchmark_carrybox_camera.py --num-envs "$size" --output "$target" --headless --enable_cameras --device cuda:0 > "$target/benchmark.log" 2>&1
  rg -q CARRYBOX_CAMERA_BENCHMARK_PASS "$target/benchmark.log"
  if [[ "$size" == 4 ]]; then
    timeout --signal=TERM --kill-after=15s 300s /home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/smoke_carrybox_walled.py --variant 4 --num-envs 4 --geometry-only --output "$output/geometry" --headless --enable_cameras --device cuda:0 > "$output/geometry/geometry.log" 2>&1
    rg -q CARRYBOX_WALLED_SMOKE_PASS "$output/geometry/geometry.log"
  fi
done
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$output/pose4/benchmark.log" "$output/scale4096/benchmark.log" "$output/geometry/geometry.log"; then
  exit 1
fi
