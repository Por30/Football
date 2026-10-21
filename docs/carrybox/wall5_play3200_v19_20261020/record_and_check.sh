#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall5_play3200_v19_20261020
free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0)
if ((free_mib < 4096)); then echo "Insufficient recording GPU memory: $free_mib MiB" >&2; exit 2; fi
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
timeout --kill-after=10s 600s /home/cao/ENTER/envs/ball/bin/python -u "$out/record.py" --headless --enable_cameras --device cuda:0 > "$out/record.log" 2>&1
rg -q RECORD_PASS "$out/record.log"
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/record.log"; then exit 1; fi
/home/cao/ENTER/envs/ball/bin/python "$out/verify.py" > "$out/verify.log" 2>&1
