#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0)
if ((free_mib < 4096)); then echo "Insufficient replay GPU memory: $free_mib MiB" >&2; exit 2; fi
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out=docs/carrybox/wall5_loco_early_20261019
for mode in policy hold_reference default_pose follow_reference hold_reference_zero_velocity; do
  timeout --kill-after=10s 110s /home/cao/ENTER/envs/ball/bin/python -u "$out/replay.py" --case "$mode" --headless --device cuda:0 > "$out/replay_$mode.log" 2>&1
  rg -q LOCO_REPLAY_PASS "$out/replay_$mode.log"
  if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/replay_$mode.log"; then exit 1; fi
done
/home/cao/ENTER/envs/ball/bin/python "$out/merge.py"
