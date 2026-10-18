#!/usr/bin/env bash
set -euo pipefail
cd /home/cao/perceptual_ball
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
export PYTHONPATH="$PWD/tests:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
/home/cao/ENTER/envs/ball/bin/python -m unittest test_carrybox_ground test_carrybox_walled test_carrybox_g1_reset -v > docs/carrybox/wall5_hold_rsi_20261017/cpu.log 2>&1
