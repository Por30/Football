#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
export PYTHONPATH="$PWD/source/perceptual_ball:$PWD/tests:${PYTHONPATH:-}"
/home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_reset_bug test_carrybox_training_v12 test_carrybox_asymmetric test_carrybox_wall5 test_carrybox_walled test_carrybox test_carrybox_push -v > docs/carrybox/wall5_reset_bug_20261019/check.log 2>&1
/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_reset_bug_20261019/audit_baseline.py
