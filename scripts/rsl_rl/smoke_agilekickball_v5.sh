#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out="${V5_SMOKE_OUTPUT:-docs/agilekickball_v5/validation}"
mkdir -p "$out"
timeout --signal=TERM --kill-after=15s 600s /home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/smoke_agilekickball_v5.py --headless --enable_cameras --device cuda:0 --output "$out" > "$out/run.log" 2>&1
rg -q AGILEKICKBALL_V5_PASS "$out/run.log"
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/run.log"; then exit 1; fi
