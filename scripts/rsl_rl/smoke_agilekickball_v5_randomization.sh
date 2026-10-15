#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
export V5_SMOKE_OUTPUT=docs/agilekickball_v5/randomization/validation
bash scripts/rsl_rl/smoke_agilekickball_v5.sh
