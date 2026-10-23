#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall5_physhsi_20261022
PYTHONPATH="$PWD/tests:$PWD/source/perceptual_ball:${PYTHONPATH:-}" /home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_physhsi test_carrybox_grasp test_carrybox_amp test_carrybox_depth_metres > "$out/cpu.log" 2>&1
/home/cao/ENTER/envs/ball/bin/python "$out/source_receipt.py" --record
printf 'CPU_PASS\n' > "$out/cpu_pass"
