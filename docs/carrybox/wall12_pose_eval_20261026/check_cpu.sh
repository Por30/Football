#!/usr/bin/env bash
set -euo pipefail
cd /home/cao/perceptual_ball
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=1
/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall12_pose_eval_20261026/analyze.py > docs/carrybox/wall12_pose_eval_20261026/analysis.log 2>&1
bash -n scripts/rsl_rl/play_carrybox_walled.sh
