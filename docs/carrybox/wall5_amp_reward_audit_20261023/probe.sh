#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
audit_dir=docs/carrybox/wall5_amp_reward_audit_20261023
free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0)
if ((free_mib < 6144)); then echo "Insufficient GPU memory: $free_mib" >&2; exit 2; fi
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
for mode in current rev22 no_delay; do
 timeout --kill-after=10s 600s /home/cao/ENTER/envs/ball/bin/python -u "$audit_dir/probe.py" --mode "$mode" --headless --device cuda:0 > "$audit_dir/probe_$mode.log" 2>&1
 rg -q PROBE_PASS "$audit_dir/probe_$mode.log"
 if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$audit_dir/probe_$mode.log"; then exit 1; fi
done
/home/cao/ENTER/envs/ball/bin/python "$audit_dir/summarize.py"
