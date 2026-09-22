#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
mkdir -p docs/agilekickball/training_audit_20260921
rm -f docs/agilekickball/training_audit_20260921/replay.json
/home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/audit_agilekickball.py --headless --device cpu > docs/agilekickball/training_audit_20260921/replay.log 2>&1
test -s docs/agilekickball/training_audit_20260921/replay.json
