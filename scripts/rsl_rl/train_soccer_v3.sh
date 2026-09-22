#!/usr/bin/env bash
# Local Isaac Sim / IsaacLab environment used by the validated v3 smoke.
set -eo pipefail
cd "$(dirname "$0")/../.."
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
exec /home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/train.py \
    --task Template-Perceptual-Ball-Soccer-v3 --headless --device cuda:0 \
    --num_envs 256 --seed 42 --logger tensorboard "$@"
