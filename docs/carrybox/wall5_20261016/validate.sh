#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out=docs/carrybox/wall5_20261016
# Small integration check only; do not interrupt the existing 4096-env wall4 run.
timeout --kill-after=10s 600s /home/cao/ENTER/envs/ball/bin/python -u "$out/validate.py" --headless --device cuda:0 > "$out/smoke.log" 2>&1
rg -q WALL5_SMOKE_PASS "$out/smoke.log"
