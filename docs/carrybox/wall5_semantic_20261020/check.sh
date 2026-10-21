#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
export PYTHONPATH="$PWD/source/perceptual_ball:$PWD/tests:${PYTHONPATH:-}"
out=docs/carrybox/wall5_semantic_20261020
rm -f "$out/check.json"
/home/cao/ENTER/envs/ball/bin/python -m unittest \
    test_carrybox_reward_geometry test_carrybox_distance3d test_carrybox_x2 \
    test_carrybox_reset_bug test_carrybox_training_v12 test_carrybox_asymmetric \
    test_carrybox_wall5 test_carrybox_walled -v > "$out/check.log" 2>&1
/home/cao/ENTER/envs/ball/bin/python "$out/source_receipt.py"
