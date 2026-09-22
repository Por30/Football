#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
/home/cao/ENTER/envs/ball/bin/python -u docs/agilekickball_v1/training_audit_20260922/replay_diagnostic.py --headless --device cpu > docs/agilekickball_v1/training_audit_20260922/replay.log 2>&1
test -s docs/agilekickball_v1/training_audit_20260922/replay.json
