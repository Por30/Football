"""Stop only the user-authorized, identity-matched old wall5 process."""
from pathlib import Path
from datetime import datetime
import hashlib, json, os, re, signal, time

DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
before = json.loads((DOC/'before.json').read_text())
pid = before['training_pid']

def alive():
    p = Path(f'/proc/{pid}')
    try:
        command = [a.decode() for a in (p/'cmdline').read_bytes().split(b'\0') if a]
        if not command:
            return False
        ticks = (p/'stat').read_text().split(') ',1)[1].split()[19]
    except FileNotFoundError:
        return False
    assert command == before['training_command'] and ticks == before['process_start_ticks'], (pid, command)
    return True

assert not (DOC/'launch.json').exists()
for path, digest in before['source_sha256'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
signals=[]
for sig, seconds in ((signal.SIGINT,20),(signal.SIGTERM,15),(signal.SIGKILL,5)):
    if not alive():
        break
    os.kill(pid, sig)
    signals.append(dict(signal=sig.name, sent_at=datetime.now().astimezone().isoformat()))
    print('STOP_SENT', pid, sig.name, flush=True)
    until=time.monotonic()+seconds
    while time.monotonic()<until and alive():
        time.sleep(.5)
assert not alive(), 'Old training has not exited'
log=Path(before['training_log']).read_text()
iterations=re.findall(r'Learning iteration (\d+)/40000',log)
checkpoint=max(Path(before['run']).glob('model_*.pt'),key=lambda p:int(p.stem.split('_')[1]))
record=dict(pid=pid,command=before['training_command'],process_start_ticks=before['process_start_ticks'],
    stopped_at=datetime.now().astimezone().isoformat(),status='exited',signals=signals,
    old_log=before['training_log'],old_run=before['run'],last_log_iteration=int(iterations[-1]),
    last_saved_checkpoint=str(checkpoint),last_saved_checkpoint_size=checkpoint.stat().st_size,
    checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
    authorization='User explicitly requested stopping current training and starting a new run')
(DOC/'stopped_run.json').write_text(json.dumps(record,indent=2)+'\n')
print('OLD_TRAIN_EXITED',json.dumps(record),flush=True)
