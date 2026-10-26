#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
exec /home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/train.py \
 --task Template-Perceptual-Ball-Kickball-v11 --num_envs 4096 \
 --device cuda:0 --headless --max_iterations 20000 --seed 42 \
 --run_name wall11_return5_aux_standing "$@"
