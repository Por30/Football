#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0)
if ((free_mib < 4096)); then
  echo "Insufficient free GPU memory for isolated replay: $free_mib MiB"
  exit 2
fi
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
timeout --kill-after=10s 600s /home/cao/ENTER/envs/ball/bin/python -u docs/carrybox/wall5_length_20261016/replay.py --headless --device cuda:0 > docs/carrybox/wall5_length_20261016/replay.log 2>&1
rg -q WALL5_REPLAY_PASS docs/carrybox/wall5_length_20261016/replay.log
