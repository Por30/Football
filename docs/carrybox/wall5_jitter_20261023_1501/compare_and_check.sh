#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall5_jitter_20261023_1501
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
for mode in no_self no_delay; do
  timeout --kill-after=10s 300s /home/cao/ENTER/envs/ball/bin/python -u "$out/compare.py" --mode "$mode" --headless --device cuda:0 > "$out/$mode.log" 2>&1
  rg -q COMPARE_PASS "$out/$mode.log"
  if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/$mode.log"; then exit 1; fi
done
/home/cao/ENTER/envs/ball/bin/python "$out/analyze_jitter.py" > "$out/jitter_analysis.log" 2>&1
