#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out=docs/carrybox/wall10_perf_20261023
timeout --kill-after=10s 500s /home/cao/ENTER/envs/ball/bin/python -u "$out/smoke.py" --headless --device cuda:0 > "$out/smoke.log" 2>&1
rg -q WALL10_SMOKE_PASS "$out/smoke.log"
timeout --kill-after=15s 1200s bash "$out/run_sim.sh" --phase candidate100 --also24 > "$out/candidate100.log" 2>&1
rg -q WALL10_PERF_PASS "$out/candidate100.log"
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/smoke.log" "$out/candidate100.log"; then exit 1; fi
