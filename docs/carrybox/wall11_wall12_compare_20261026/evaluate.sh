#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
[[ "$free_mib" -ge 6000 ]] || { echo 'Insufficient free GPU memory'; exit 2; }
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out=docs/carrybox/wall11_wall12_compare_20261026
for seed in 12345 67890; do
  for variant in 11 12; do
    log="$out/wall${variant}_seed${seed}.log"
    timeout --kill-after=10s 360s /home/cao/ENTER/envs/ball/bin/python -u "$out/evaluate.py" --variant "$variant" --eval_seed "$seed" --headless --device cuda:0 > "$log" 2>&1
    rg -q PAIR_EVAL_PASS "$log"
    if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$log"; then exit 1; fi
  done
done
