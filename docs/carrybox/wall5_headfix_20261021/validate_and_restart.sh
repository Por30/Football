#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall5_headfix_20261021
python_bin=/home/cao/ENTER/envs/ball/bin/python
"$python_bin" "$out/source_receipt.py"
if [[ ! -f "$out/cpu_pass" ]]; then
    PYTHONPATH="$PWD/source/perceptual_ball:$PWD/tests" OMP_NUM_THREADS=2 "$python_bin" -m unittest test_carrybox_reward_geometry test_carrybox_distance3d test_carrybox_wall_parity test_carrybox_x2 test_carrybox_reset_bug test_carrybox_training_v12 test_carrybox_asymmetric test_carrybox_wall5 test_carrybox_walled -v > "$out/cpu.log" 2>&1
    touch "$out/cpu_pass"
fi
if [[ ! -f "$out/smoke_pass" ]]; then
    bash "$out/smoke.sh"
fi
"$python_bin" "$out/source_receipt.py"
bash "$out/start_and_verify.sh"
