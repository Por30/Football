#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
bash -n docs/carrybox/wall5_rev14_play_20261019/play.sh
export PYTHONPATH="$PWD/source/perceptual_ball:$PWD/tests:${PYTHONPATH:-}"
/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_rev14_play_20261019/check.py > docs/carrybox/wall5_rev14_play_20261019/check.log 2>&1
