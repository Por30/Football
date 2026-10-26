#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
export PYTHONPATH="$PWD/tests:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
/home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_wall13 test_carrybox_wall12 test_carrybox_wall11 test_state_feedback test_kickball_v11 > docs/carrybox/wall13_feedback_20261026/cpu.log 2>&1
/home/cao/ENTER/envs/ball/bin/python -m py_compile scripts/rsl_rl/train.py scripts/rsl_rl/play.py
