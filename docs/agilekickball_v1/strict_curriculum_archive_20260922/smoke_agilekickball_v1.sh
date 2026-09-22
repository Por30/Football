#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
mkdir -p docs/agilekickball_v1/validation
rm -f docs/agilekickball_v1/validation/smoke.json
/home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/smoke_agilekickball_v1.py --headless --device cpu > docs/agilekickball_v1/validation/smoke.log 2>&1
test -s docs/agilekickball_v1/validation/smoke.json
