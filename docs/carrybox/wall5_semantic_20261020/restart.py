"""Authorized restart only after both checks pass; signal the exact previous run."""
from datetime import datetime
import json
from pathlib import Path
import signal
import time
import validate_sources

DOC = Path(__file__).resolve().parent
assert (DOC/'smoke_pass').exists()
assert json.loads((DOC/'smoke.json').read_text())['status'] == 'PASS'
assert not (DOC/'launch.json').exists(), 'Do not start twice'
old = json.loads((DOC.parent/'wall5_v18_fresh_20261020/launch.json').read_text())
pid = old['pid']
proc = Path(f'/proc/{pid}')
def running():
    try:
        return proc.joinpath('stat').read_text().split()[2] != 'Z'
    except FileNotFoundError:
        return False

if running():
    actual = [a.decode() for a in proc.joinpath('cmdline').read_bytes().split(b'\0') if a]
    assert actual == old['command'], (actual, old['command'])
    old['proc_start_ticks'] = proc.joinpath('stat').read_text().split()[21]
    # SIGINT lets the launcher/application shut down cleanly.
    import os
    os.kill(pid, signal.SIGINT)
    for _ in range(60):
        if not running():
            break
        time.sleep(1)
    assert not running(), 'Previous training did not exit; do not launch another'
elif (DOC/'stopped_run.json').exists():
    print('PREVIOUS_RUN_ALREADY_STOPPED', pid, flush=True)
    raise SystemExit(0)
old['stopped_at'] = datetime.now().astimezone().isoformat()
old['signal'] = 'SIGINT'
old['historical_artifacts_preserved'] = True
(DOC/'stopped_run.json').write_text(json.dumps(old, indent=2)+'\n')
print('PREVIOUS_RUN_STOPPED', pid, flush=True)
