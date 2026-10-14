#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../.."
bash scripts/rsl_rl/smoke_carrybox_walled.sh
# Bound the concurrent diagnostic to protect the existing football job. Only
# this new process group may be stopped; queue repeats 128 after football exits.
/home/cao/ENTER/envs/ball/bin/python - <<'PY'
import json, os, signal, subprocess, time
from pathlib import Path

def used_free():
    return [int(x) for x in subprocess.check_output(['nvidia-smi','--id=0','--query-gpu=memory.used,memory.free','--format=csv,noheader,nounits'],text=True).strip().split(',')]
base, free = used_free()
if free < 7000:
    raise RuntimeError('Insufficient GPU headroom for concurrent 128-env acceptance; wait for football')
env = os.environ.copy()
env.update(WALLED_VARIANTS='4', WALLED_SCALE_PREFLIGHT='1')
child = subprocess.Popen(['bash','scripts/rsl_rl/smoke_carrybox_walled.sh'],env=env,start_new_session=True)
peak = base
start = time.monotonic()
try:
    while child.poll() is None:
        used, free = used_free()
        peak = max(peak, used)
        if free < 1024 or time.monotonic()-start > 1260:
            raise RuntimeError('128-env acceptance memory/time guard reached')
        time.sleep(3)
    if child.returncode:
        raise RuntimeError(f'128-env acceptance failed: {child.returncode}')
    Path('docs/carrybox/wall4_repair/scale128/memory.json').write_text(json.dumps(dict(status='PASS',baseline_used_mib=base,peak_total_used_mib=peak,increment_mib=peak-base),indent=2)+'\n')
except BaseException:
    if child.poll() is None:
        os.killpg(child.pid,signal.SIGKILL)
        child.wait()
    raise
PY
