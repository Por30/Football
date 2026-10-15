#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
timeout --kill-after=10s 900s /home/cao/ENTER/envs/ball/bin/python -u docs/carrybox/convergence_20261015/replay.py --headless --device cuda:0 > docs/carrybox/convergence_20261015/replay.log 2>&1
rg -q WALL4_DIAGNOSIS_PASS docs/carrybox/convergence_20261015/replay.log
