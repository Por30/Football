#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
mkdir -p docs/agilekickball/learning_validation
rm -f docs/agilekickball/learning_validation/result.json
if ! /home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/validate_agilekickball_learning.py --headless --device cpu > docs/agilekickball/learning_validation/run.log 2>&1; then
    tail -60 docs/agilekickball/learning_validation/run.log
    exit 1
fi
test -s docs/agilekickball/learning_validation/result.json
