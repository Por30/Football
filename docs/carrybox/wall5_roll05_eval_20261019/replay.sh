#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out=docs/carrybox/wall5_roll05_eval_20261019
for mode in mean sample; do
  replay_free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0)
  if ((replay_free_mib < 6000)); then echo "Insufficient diagnostic GPU memory: $replay_free_mib MiB" >&2; exit 2; fi
  timeout --kill-after=10s 240s /home/cao/ENTER/envs/ball/bin/python -u "$out/replay.py" --mode "$mode" --headless --device cuda:0 > "$out/replay_$mode.log" 2>&1
  rg -q LOCO_EVAL_PASS "$out/replay_$mode.log"
  if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/replay_$mode.log"; then exit 1; fi
done
/home/cao/ENTER/envs/ball/bin/python "$out/summarize.py"
