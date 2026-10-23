#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall5_reset_audit_20261022
/home/cao/ENTER/envs/ball/bin/python "$out/analyze.py" > "$out/analyze.log" 2>&1
free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0)
if ((free < 4096)); then echo 'Insufficient memory for reset probe'; exit 2; fi
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
timeout --kill-after=10s 600s /home/cao/ENTER/envs/ball/bin/python -u "$out/probe.py" --headless --device cuda:0 > "$out/probe.log" 2>&1
rg -q RESET_PROBE_PASS "$out/probe.log"
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/probe.log"; then exit 1; fi
/home/cao/ENTER/envs/ball/bin/python "$out/summarize.py"
