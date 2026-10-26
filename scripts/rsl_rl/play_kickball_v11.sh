#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
checkpoint=${1:?Usage: play_kickball_v11.sh CHECKPOINT [NUM_ENVS] [extra args]}
num_envs=${2:-4}
shift
if [[ $# -gt 0 ]]; then shift; fi
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
exec /home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/play.py \
 --task Template-Perceptual-Ball-Kickball-v11 --num_envs "$num_envs" \
 --device cuda:0 --checkpoint "$checkpoint" "$@"
