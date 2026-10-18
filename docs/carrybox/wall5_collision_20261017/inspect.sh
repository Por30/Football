#!/usr/bin/env bash
set -euo pipefail
cd /home/cao/perceptual_ball
usd_lib=/home/cao/isaacsim/extscache/omni.usd.libs-1.0.1+d02c707b.lx64.r.cp310
export PYTHONPATH="$usd_lib:${PYTHONPATH:-}"
export LD_LIBRARY_PATH="$usd_lib/bin:/home/cao/isaacsim/kit:${LD_LIBRARY_PATH:-}"
/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_collision_20261017/audit_geometry.py > docs/carrybox/wall5_collision_20261017/audit.log 2>&1
