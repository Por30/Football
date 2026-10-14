#!/usr/bin/env bash
# Formal single-GPU recipe. Extra CLI/Hydra arguments follow the defaults.
set -eo pipefail
cd "$(dirname "$0")/../.."
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
initialization=(--warm_start_v2 /home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v2/2026-09-25_22-18-55_v1_speed_only_20260925_scratch/model_49999.pt)
for argument in "$@"; do
  if [[ "$argument" == "--resume" ]]; then initialization=(); fi
done
if [[ "${V3_SCRATCH:-0}" == "1" ]]; then initialization=(); fi
exec /home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/train.py \
  --task Template-Perceptual-Ball-AgileKickball-v3 \
  --num_envs 4096 --device cuda:0 --headless \
  --max_iterations 50000 --seed 42 \
  --run_name feedback_stable_20261008_v2init "${initialization[@]}" "$@"
