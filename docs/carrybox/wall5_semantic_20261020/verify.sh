#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall5_semantic_20261020
if [[ ! -f "$out/launch.json" ]]; then
    /home/cao/ENTER/envs/ball/bin/python "$out/restart.py" > "$out/restart.log" 2>&1
    bash "$out/launch.sh" >> "$out/restart.log" 2>&1
fi
/home/cao/ENTER/envs/ball/bin/python -u "$out/verify.py" > "$out/verify.log" 2>&1
