#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
variant="${CARRYBOX_VARIANT:-4}"
case "$variant" in 3|4|5|10|11|12) ;; *) echo 'CARRYBOX_VARIANT must be 3, 4, 5, 10, 11 or 12' >&2; exit 2;; esac
default_envs=128
if [[ "$variant" == 10 || "$variant" == 11 || "$variant" == 12 ]]; then default_envs=4096; fi
source "${ISAAC_SIM_PATH:-/home/cao/isaacsim}/setup_conda_env.sh"
lab_root="${ISAAC_LAB_PATH:-/home/cao/IsaacLab}"
export PYTHONPATH="$lab_root/source/isaaclab:$lab_root/source/isaaclab_rl:$lab_root/source/isaaclab_tasks:$lab_root/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
exec "${BALL_PYTHON:-/home/cao/ENTER/envs/ball/bin/python}" -u scripts/rsl_rl/train.py \
  --task "Template-Perceptual-Ball-CarryBox-Walled${variant}-v0" \
  --num_envs "$default_envs" --device cuda:0 --headless --seed 42 "$@"
