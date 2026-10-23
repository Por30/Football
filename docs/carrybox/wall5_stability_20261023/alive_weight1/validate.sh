#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall5_stability_20261023
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
/home/cao/ENTER/envs/ball/bin/python "$out/source_receipt.py" --record
PYTHONPATH="$PWD/tests:$PYTHONPATH" /home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_wall5_stability test_carrybox_physhsi > "$out/cpu.log" 2>&1
timeout --kill-after=10s 1200s /home/cao/ENTER/envs/ball/bin/python -u "$out/validate.py" --headless --device cuda:0 > "$out/validate.log" 2>&1
rg -q STABILITY_VALIDATION_PASS "$out/validate.log"
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/validate.log"; then exit 1; fi
/home/cao/ENTER/envs/ball/bin/python "$out/source_receipt.py"
printf 'SMOKE_PASS\n' > "$out/smoke_pass"
