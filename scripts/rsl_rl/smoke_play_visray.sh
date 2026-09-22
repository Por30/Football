#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
mkdir -p docs/play_visray
rm -f docs/play_visray/smoke.json
/home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/smoke_play_visray.py --headless --enable_cameras --device cpu > docs/play_visray/smoke.log 2>&1
test -s docs/play_visray/smoke.json
