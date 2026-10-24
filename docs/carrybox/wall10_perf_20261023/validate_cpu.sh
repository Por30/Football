#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
export PYTHONPATH="$PWD/tests:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
/home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_wall10_perf test_carrybox_wall10 test_carrybox test_carrybox_amp test_soccer_v3 > docs/carrybox/wall10_perf_20261023/cpu.log 2>&1
