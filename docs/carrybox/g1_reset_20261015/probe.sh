#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
timeout --kill-after=10s 900s /home/cao/ENTER/envs/ball/bin/python -u docs/carrybox/g1_reset_20261015/probe.py --headless --device cuda:0 > docs/carrybox/g1_reset_20261015/probe.log 2>&1
rg -q PROBE_DONE docs/carrybox/g1_reset_20261015/probe.log
