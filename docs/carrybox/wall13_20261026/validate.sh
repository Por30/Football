#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
bash -n scripts/rsl_rl/train_carrybox_walled.sh scripts/rsl_rl/play_carrybox_walled.sh
free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
[[ "$free_mib" -ge 6000 ]] || { echo 'Insufficient GPU memory for wall13 smoke'; exit 2; }
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out=docs/carrybox/wall13_20261026
timeout --kill-after=10s 300s /home/cao/ENTER/envs/ball/bin/python -u "$out/smoke.py" --headless --device cuda:0 > "$out/smoke.log" 2>&1
rg -q WALL13_SMOKE_PASS "$out/smoke.log"
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/smoke.log"; then exit 1; fi
