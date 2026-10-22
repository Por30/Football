#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
diag=docs/carrybox/wall5_walk_diagnosis_20261022
free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0)
if ((free_mib < 6144)); then echo "Insufficient diagnostic GPU memory" >&2; exit 2; fi
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
for collision in on off; do
  timeout --kill-after=10s 600s /home/cao/ENTER/envs/ball/bin/python -u "$diag/replay.py" --collision "$collision" --headless --device cuda:0 > "$diag/$collision.log" 2>&1
  rg -q REPLAY_PASS "$diag/$collision.log"
  if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$diag/$collision.log"; then exit 1; fi
done
/home/cao/ENTER/envs/ball/bin/python "$diag/verify.py"
