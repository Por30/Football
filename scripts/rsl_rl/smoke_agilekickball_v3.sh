#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
mkdir -p docs/agilekickball_v3/stability_fix_20261008
rm -f docs/agilekickball_v3/stability_fix_20261008/smoke.json
/home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/smoke_agilekickball_v3.py --headless --device cpu > docs/agilekickball_v3/stability_fix_20261008/smoke.log 2>&1
test -s docs/agilekickball_v3/stability_fix_20261008/smoke.json
# Exercise the exact formal launcher / Hydra / logger / checkpoint path at bounded GPU scale.
bash scripts/rsl_rl/train_agilekickball_v3.sh --num_envs 4096 --max_iterations 100 \
  --run_name feedback_stable_scale_smoke agent.experiment_name=agilekickball_v3_smoke \
  > docs/agilekickball_v3/stability_fix_20261008/train_launch.log 2>&1
/home/cao/ENTER/envs/ball/bin/python docs/agilekickball_v3/stability_fix_20261008/verify_scale.py
