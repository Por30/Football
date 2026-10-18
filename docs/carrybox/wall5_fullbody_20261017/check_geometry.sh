#!/usr/bin/env bash
set -euo pipefail
cd /home/cao/perceptual_ball
usd_lib=/home/cao/isaacsim/extscache/omni.usd.libs-1.0.1+d02c707b.lx64.r.cp310
export PYTHONPATH="$usd_lib:${PYTHONPATH:-}"
export LD_LIBRARY_PATH="$usd_lib/bin:/home/cao/isaacsim/kit:${LD_LIBRARY_PATH:-}"
export OPENBLAS_NUM_THREADS=2
export OMP_NUM_THREADS=2
/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_fullbody_20261017/check_geometry.py > docs/carrybox/wall5_fullbody_20261017/geometry.log 2>&1
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p 'test_carrybox_wall5.py' -v > docs/carrybox/wall5_fullbody_20261017/cpu.log 2>&1
