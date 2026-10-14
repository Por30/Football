"""Launch the authorized scratch run once, after all frozen checks have passed."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

out = Path(__file__).resolve().parent
root = out.parents[2]
receipts = json.loads((out / 'receipts.json').read_text())['tests']
assert len(receipts) == 3 and all(row['result'] == 'PASS' and row['exit_code'] == 0 for row in receipts)
assert not (out / 'launch.json').exists(), 'A launch has already been recorded; inspect it first'
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():
        continue
    try:
        args = (proc / 'cmdline').read_bytes().split(b'\0')
    except (OSError, PermissionError):
        continue
    assert b'scripts/rsl_rl/train.py' not in args, 'Another training process is still active: ' + proc.name
now = datetime.now(ZoneInfo('Asia/Tokyo'))
log = root / 'logs/background' / ('agilekickball_v3_feedback_stable_' + now.strftime('%Y%m%d_%H%M%S') + '.log')
log.parent.mkdir(parents=True, exist_ok=True)
command = ['bash', str(root / 'scripts/rsl_rl/train_agilekickball_v3.sh')]
with log.open('xb') as stream:
    process = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
stat = Path(f'/proc/{process.pid}/stat').read_text().split(') ', 1)[1].split()
allowed = json.loads((out / 'allowed_paths.json').read_text())
hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
          for name in allowed if (root / name).is_file() and name.endswith(('.py', '.sh'))}
meta = dict(pid=process.pid, start_ticks=int(stat[19]), session_id=os.getsid(process.pid),
            started_at_jst=now.isoformat(), command=command, log=str(log), cwd=str(root),
            task='Template-Perceptual-Ball-AgileKickball-v3', revision='feedback_stable_20261008',
            num_envs=4096, max_iterations=50000, seed=42, resume=False, initialization='v2_weights_only', source_sha256=hashes)
(out / 'launch.json').write_text(json.dumps(meta, indent=2) + '\n')
log.with_suffix('.pid').write_text(str(process.pid) + '\n')
print(json.dumps(meta, indent=2))
