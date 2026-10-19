#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
/home/cao/ENTER/envs/ball/bin/python -u docs/carrybox/wall5_roll05_eval_20261019/check.py > docs/carrybox/wall5_roll05_eval_20261019/check.log 2>&1
