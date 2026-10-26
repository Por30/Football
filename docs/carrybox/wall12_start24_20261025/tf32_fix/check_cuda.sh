#!/usr/bin/env bash
set -euo pipefail
cd /home/cao/perceptual_ball
/home/cao/ENTER/envs/ball/bin/python tests/test_carrybox_wall12_tf32.py > docs/carrybox/wall12_start24_20261025/tf32_fix/cuda.log 2>&1
