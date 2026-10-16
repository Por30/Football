#!/usr/bin/env bash
# Small GUI replay alongside training: capacity changes only, identical task/depth.
set -eo pipefail
if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: bash $0 CHECKPOINT [NUM_ENVS=4, range 1..4]" >&2
  exit 2
fi
checkpoint="$(realpath -- "$1")"
[[ -f "$checkpoint" ]] || { echo "Checkpoint does not exist: $checkpoint" >&2; exit 2; }
num_envs="${2:-4}"
case "$num_envs" in 1|2|3|4) ;; *) echo 'Small-memory replay supports 1 to 4 environments' >&2; exit 2;; esac
variant="${CARRYBOX_VARIANT:-4}"
case "$variant" in 3|4|5) ;; *) echo 'CARRYBOX_VARIANT must be 3, 4 or 5' >&2; exit 2;; esac
cd "$(dirname "$0")/../.."
source "${ISAAC_SIM_PATH:-/home/cao/isaacsim}/setup_conda_env.sh"
lab_root="${ISAAC_LAB_PATH:-/home/cao/IsaacLab}"
export PYTHONPATH="$lab_root/source/isaaclab:$lab_root/source/isaaclab_rl:$lab_root/source/isaaclab_tasks:$lab_root/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
exec "${BALL_PYTHON:-/home/cao/ENTER/envs/ball/bin/python}" -u scripts/rsl_rl/play.py \
  --task "Template-Perceptual-Ball-CarryBox-Walled${variant}-v0" \
  --num_envs "$num_envs" --device cuda:0 --real-time --rendering_mode performance \
  --checkpoint "$checkpoint" \
  --kit_args "--/app/window/width=960 --/app/window/height=640 --/app/renderer/resolution/width=960 --/app/renderer/resolution/height=540" \
  env.sim.physx.gpu_found_lost_pairs_capacity=262144 \
  env.sim.physx.gpu_found_lost_aggregate_pairs_capacity=262144 \
  env.sim.physx.gpu_total_aggregate_pairs_capacity=262144
