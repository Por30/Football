#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
export PYTHONPATH="$PWD/tests:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
out=docs/carrybox/wall10_perf_20261023
timeout --kill-after=10s 300s /home/cao/ENTER/envs/ball/bin/python -u "$out/benchmark_learning.py" > "$out/learning.log" 2>&1
rg -q WALL10_LEARNING_PASS "$out/learning.log"
