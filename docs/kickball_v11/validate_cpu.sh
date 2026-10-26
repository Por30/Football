#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
export PYTHONPATH="$PWD/tests:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
/home/cao/ENTER/envs/ball/bin/python -m unittest test_kickball_v11 test_carrybox_wall10 test_carrybox_wall10_perf test_carrybox_wall11 test_agilekickball_v4 > docs/kickball_v11/cpu.log 2>&1
bash -n scripts/rsl_rl/train_kickball_v11.sh scripts/rsl_rl/play_kickball_v11.sh
/home/cao/ENTER/envs/ball/bin/python -m py_compile scripts/rsl_rl/train.py scripts/rsl_rl/play.py source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/kickball_v11_env_cfg.py source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_v11.py
