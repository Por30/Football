#!/usr/bin/env bash
set -euo pipefail
cd /home/cao/perceptual_ball
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=1
/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall13_concat_20261026/check_training.py > docs/carrybox/wall13_concat_20261026/health_check.log 2>&1
