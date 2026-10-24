#!/usr/bin/env bash
set -eo pipefail
cd /home/cao/perceptual_ball
out=docs/carrybox/wall10_play4_20261024_1130
if [[ -f "$out/recording.json" ]]; then
  # Resume post-processing after an interrupted caller; preserve the completed video.
  /home/cao/ENTER/envs/ball/bin/python - "$out" <<'PY'
import hashlib, json, sys
from pathlib import Path
out = Path(sys.argv[1])
r = json.loads((out / 'recording.json').read_text())
s = json.loads((out / 'selection.json').read_text())
assert r['status'] == 'PASS' and r['checkpoint_sha256'] == s['checkpoint_sha256']
assert r['video'] == s['video'] and Path(r['video']).is_file()
assert hashlib.sha256(Path(s['checkpoint']).read_bytes()).hexdigest() == s['checkpoint_sha256']
for path, expected in s['source_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected
PY
else
free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0)
if ((free_mib < 6144)); then echo "Insufficient recording GPU memory: $free_mib MiB" >&2; exit 2; fi
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
timeout --kill-after=10s 900s /home/cao/ENTER/envs/ball/bin/python -u "$out/record.py" --headless --enable_cameras --device cuda:0 > "$out/record.log" 2>&1
fi
rg -q RECORD_PASS "$out/record.log"
if rg -i 'Traceback \(most recent call last\)|PhysX error|illegal memory access|CUDA error:|out of memory' "$out/record.log"; then exit 1; fi
/home/cao/ENTER/envs/ball/bin/python "$out/verify.py" > "$out/verify.log" 2>&1

/home/cao/ENTER/envs/ball/bin/python "$out/analyze_behavior.py" > "$out/analyze.log" 2>&1

/home/cao/ENTER/envs/ball/bin/python "$out/prepare_video.py" > "$out/prepare_video.log" 2>&1
