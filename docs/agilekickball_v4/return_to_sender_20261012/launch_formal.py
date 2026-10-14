"""Launch exactly one authorized v4 training only after the frozen preflight passed."""
import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

root = Path('/home/cao/perceptual_ball')
out = root / 'docs/agilekickball_v4/return_to_sender_20261012'
receipts = json.loads((out / 'receipts.json').read_text())['tests']
assert len(receipts) == 3 and all(x['result'] == 'PASS' and x['exit_code'] == 0 for x in receipts)
smoke = json.loads((out / 'smoke.json').read_text())
scale = json.loads((out / 'scale.json').read_text())
assert smoke['revision'] == 'return_to_sender_20261012' and scale['iterations'] == 100
for line in subprocess.check_output(['ps', '-eo', 'pid,args'], text=True).splitlines():
    fields = line.split(maxsplit=1)
    if len(fields) == 2:
        try: args = shlex.split(fields[1])
        except ValueError: continue
        assert not any(arg.endswith('/rsl_rl/train.py') for arg in args), 'Existing training: ' + line
log = root / 'logs/rsl_rl/agilekickball_v4/train_20261012.log'
log.parent.mkdir(parents=True, exist_ok=True)
command = ['nohup', 'bash', 'scripts/rsl_rl/train_agilekickball_v4.sh']
with log.open('x') as stream:
    proc = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL, stdout=stream,
                            stderr=subprocess.STDOUT, start_new_session=True)
receipt = dict(pid=proc.pid, command=command, log=str(log),
               started_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
               initialization=smoke['initialization'],
               receipt_file=str(out / 'receipts.json'))
(out / 'launch.json').write_text(json.dumps(receipt, indent=2) + '\n')
(log.parent / 'train_20261012.pid').write_text(str(proc.pid) + '\n')
print(json.dumps(receipt, indent=2))
