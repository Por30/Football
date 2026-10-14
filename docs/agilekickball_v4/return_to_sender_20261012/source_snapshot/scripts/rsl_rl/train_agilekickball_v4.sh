#!/usr/bin/env bash
# Independent v4 experiment; initialize all stable v3 weights, never its optimizer/course.
set -eo pipefail
cd "$(dirname "$0")/../.."
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
initialization=(--warm_start_v3 /home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v3/2026-10-08_11-48-24_feedback_stable_20261008_v2init/model_49999.pt)
for argument in "$@"; do
  if [[ "$argument" == "--resume" ]]; then initialization=(); fi
done
exec /home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/train.py \
  --task Template-Perceptual-Ball-AgileKickball-v4 \
  --num_envs 4096 --device cuda:0 --headless \
  --max_iterations 50000 --seed 42 \
  --run_name return_to_sender_20261012_v3init "${initialization[@]}" "$@"
