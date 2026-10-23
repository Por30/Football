#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall5_training_audit_20261022
/home/cao/ENTER/envs/ball/bin/python "$out/analyze.py" > "$out/analyze.log" 2>&1
PYTHONPATH="$PWD/tests:$PWD/source/perceptual_ball:${PYTHONPATH:-}" /home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_critic123_aux test_carrybox_training_v12 test_carrybox_amp > "$out/cpu.log" 2>&1
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
timeout --kill-after=10s 600s /home/cao/ENTER/envs/ball/bin/python -u "$out/probe.py" --headless --device cuda:0 > "$out/probe.log" 2>&1
rg -q TRAINING_AUDIT_PASS "$out/probe.log"
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/probe.log"; then exit 1; fi
/home/cao/ENTER/envs/ball/bin/python "$out/summarize.py"
