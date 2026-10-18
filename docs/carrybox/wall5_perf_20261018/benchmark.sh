#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
rg -q '^OK$' docs/carrybox/wall5_perf_20261018/check.log
timeout --kill-after=10s 900s bash docs/carrybox/wall5_perf_20261018/run_profile.sh candidate > docs/carrybox/wall5_perf_20261018/candidate.log 2>&1
rg -q PERF_PROFILE_PASS docs/carrybox/wall5_perf_20261018/candidate.log
if rg 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|OutOfMemoryError' docs/carrybox/wall5_perf_20261018/candidate.log; then exit 1; fi
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_perf_20261018/restart.py
