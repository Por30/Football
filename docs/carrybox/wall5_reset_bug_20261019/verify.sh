#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
/home/cao/ENTER/envs/ball/bin/python -u docs/carrybox/wall5_reset_bug_20261019/verify.py > docs/carrybox/wall5_reset_bug_20261019/verify.log 2>&1
