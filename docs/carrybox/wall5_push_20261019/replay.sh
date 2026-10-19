#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0)
if ((free_mib < 4096)); then echo "Insufficient replay GPU memory: $free_mib MiB" >&2; exit 2; fi
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out=docs/carrybox/wall5_push_20261019
timeout --kill-after=10s 600s /home/cao/ENTER/envs/ball/bin/python -u "$out/replay.py" --headless --device cuda:0 > "$out/replay.log" 2>&1
rg -q PUSH_REPLAY_PASS "$out/replay.log"
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/replay.log"; then exit 1; fi
