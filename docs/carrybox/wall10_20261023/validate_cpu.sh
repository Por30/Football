#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall10_20261023
PYTHONPATH="$PWD/tests:$PWD/source/perceptual_ball:${PYTHONPATH:-}" /home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_wall10 test_carrybox test_carrybox_amp test_soccer_v3 > "$out/cpu.log" 2>&1
bash -n scripts/rsl_rl/train_carrybox_walled.sh scripts/rsl_rl/play_carrybox_walled.sh
