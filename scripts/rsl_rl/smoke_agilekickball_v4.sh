#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
out=docs/agilekickball_v4/return_to_sender_20261012
mkdir -p "$out"
/home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/smoke_agilekickball_v4.py --headless --device cpu > "$out/smoke.log" 2>&1
bash scripts/rsl_rl/train_agilekickball_v4.sh --num_envs 4096 --max_iterations 100 \
  --run_name return_to_sender_scale_smoke agent.experiment_name=agilekickball_v4_smoke \
  > "$out/scale.log" 2>&1
/home/cao/ENTER/envs/ball/bin/python "$out/verify_scale.py"
