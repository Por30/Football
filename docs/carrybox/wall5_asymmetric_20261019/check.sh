#!/usr/bin/env bash
set -euo pipefail
cd /home/cao/perceptual_ball
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
export PYTHONPATH="$PWD/tests:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
/home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_asymmetric test_carrybox_perf test_carrybox test_carrybox_wall5 test_carrybox_training_v12 test_carrybox_amp -v > docs/carrybox/wall5_asymmetric_20261019/cpu.log 2>&1
tail -6 docs/carrybox/wall5_asymmetric_20261019/cpu.log
