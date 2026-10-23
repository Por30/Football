#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall5_clean_camera_20261023
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
/home/cao/ENTER/envs/ball/bin/python "$out/source_receipt.py" --record
PYTHONPATH="$PWD/tests:$PYTHONPATH" /home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_depth_metres test_carrybox_push test_carrybox_raycast test_carrybox_wall5_stability > "$out/cpu.log" 2>&1
timeout --kill-after=10s 400s /home/cao/ENTER/envs/ball/bin/python -u "$out/smoke.py" --headless --device cuda:0 > "$out/validate.log" 2>&1
rg -q CLEAN_CAMERA_SMOKE_PASS "$out/validate.log"
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/validate.log"; then exit 1; fi
/home/cao/ENTER/envs/ball/bin/python "$out/source_receipt.py"
printf 'SMOKE_PASS\n' > "$out/smoke_pass"
