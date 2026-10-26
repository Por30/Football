#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
[[ "$free_mib" -ge 6000 ]] || { echo 'Insufficient free GPU memory'; exit 2; }
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out=docs/carrybox/wall12_pose_eval_20261026
timeout --kill-after=10s 600s /home/cao/ENTER/envs/ball/bin/python -u "$out/evaluate.py" --headless --device cuda:0 > "$out/evaluation.log" 2>&1
rg -q WALL12_POSE_EVAL_PASS "$out/evaluation.log"
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/evaluation.log"; then exit 1; fi
