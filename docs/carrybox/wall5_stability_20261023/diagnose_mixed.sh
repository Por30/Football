#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall5_stability_20261023
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
timeout --kill-after=10s 600s /home/cao/ENTER/envs/ball/bin/python -u "$out/diagnose_mixed.py" --headless --device cuda:0 > "$out/diagnose_mixed.log" 2>&1
rg -q MIXED_DIAGNOSIS_PASS "$out/diagnose_mixed.log"
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/diagnose_mixed.log"; then exit 1; fi
