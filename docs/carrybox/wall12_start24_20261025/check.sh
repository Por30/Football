#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=1
/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall12_start24_20261025/check.py
