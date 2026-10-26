#!/usr/bin/env bash
set -euo pipefail
cd /home/cao/perceptual_ball
export CUDA_VISIBLE_DEVICES=""
export PYTHONPATH="$PWD/tests:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
/home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_wall12 test_carrybox_wall11 test_carrybox_wall10 test_carrybox_wall10_perf test_carrybox test_carrybox_amp test_soccer_v3 > docs/carrybox/wall12_start24_20261025/tf32_fix/cpu.log 2>&1
