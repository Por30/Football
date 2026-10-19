#!/usr/bin/env bash
set -eo pipefail
if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: bash $0 CHECKPOINT [NUM_ENVS=4]" >&2
  exit 2
fi
checkpoint=$(realpath -- "$1")
[[ -f "$checkpoint" ]] || { echo "Checkpoint does not exist: $checkpoint" >&2; exit 2; }
num_envs=${2:-4}
case "$num_envs" in 1|2|3|4) ;; *) echo 'NUM_ENVS must be 1..4' >&2; exit 2;; esac
cd "$(dirname "$0")/../../.."
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
exec /home/cao/ENTER/envs/ball/bin/python -u docs/carrybox/wall5_rev14_play_20261019/play.py \
  --checkpoint "$checkpoint" --num_envs "$num_envs" --device cuda:0 --real-time --rendering_mode performance \
  --kit_args "--/app/window/width=1280 --/app/window/height=720"
