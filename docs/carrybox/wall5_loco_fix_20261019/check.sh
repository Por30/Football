#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
export PYTHONPATH="$PWD/source/perceptual_ball:$PWD/tests:${PYTHONPATH:-}"
/home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_loco_fix test_carrybox_push test_carrybox_asymmetric test_carrybox_wall5 test_carrybox_walled test_carrybox_amp test_carrybox -v > docs/carrybox/wall5_loco_fix_20261019/check.log 2>&1
