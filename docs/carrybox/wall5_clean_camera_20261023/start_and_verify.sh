#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall5_clean_camera_20261023
if [[ ! -f "$out/launch.json" ]]; then
    if [[ ! -f "$out/stopped_run.json" ]]; then
        /home/cao/ENTER/envs/ball/bin/python -u "$out/stop.py" > "$out/restart.log" 2>&1
    fi
    bash "$out/launch.sh" >> "$out/restart.log" 2>&1
fi
/home/cao/ENTER/envs/ball/bin/python -u "$out/verify.py" > "$out/verify.log" 2>&1
