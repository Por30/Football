#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
export PYTHONPATH="$PWD/tests:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
/home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_wall12 test_carrybox_wall11 test_carrybox_wall10 test_carrybox_wall10_perf test_carrybox test_carrybox_amp test_soccer_v3 > docs/carrybox/wall12_20261025/cpu.log 2>&1
bash -n scripts/rsl_rl/train_carrybox_walled.sh scripts/rsl_rl/play_carrybox_walled.sh
/home/cao/ENTER/envs/ball/bin/python -m py_compile scripts/rsl_rl/train.py scripts/rsl_rl/play.py source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py
