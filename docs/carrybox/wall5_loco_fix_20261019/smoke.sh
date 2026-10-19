#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0)
if ((free_mib < 19000)); then echo "Insufficient smoke GPU memory: $free_mib MiB" >&2; exit 2; fi
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out=docs/carrybox/wall5_loco_fix_20261019
for stage in physical update pilot; do
 timeout --kill-after=10s 900s /home/cao/ENTER/envs/ball/bin/python -u "$out/$stage.py" --headless --device cuda:0 > "$out/$stage.log" 2>&1
 if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/$stage.log"; then exit 1; fi
done
rg -q LOCO_PHYSICAL_PASS "$out/physical.log"
rg -q LOCO_UPDATE_PASS "$out/update.log"
rg -q LOCO_PILOT_PASS "$out/pilot.log"
