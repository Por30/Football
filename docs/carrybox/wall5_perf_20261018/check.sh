#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
export PYTHONPATH="$PWD/tests:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
/home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_perf test_carrybox_wall5 test_carrybox_ground test_carrybox_training_v12 test_carrybox_walled test_carrybox_amp > docs/carrybox/wall5_perf_20261018/check.log 2>&1
tail -6 docs/carrybox/wall5_perf_20261018/check.log
