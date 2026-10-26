"""Execute the user's one-time kickball -> fresh wall13 training switch."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from datetime import datetime

ROOT = Path('/home/cao/perceptual_ball')
OUT = Path(__file__).resolve().parent
TASK = 'Template-Perceptual-Ball-CarryBox-Walled13-v0'


def process(pid):
    p = Path('/proc') / str(pid)
    args = [v.decode() for v in (p / 'cmdline').read_bytes().split(b'\0') if v]
    stat = (p / 'stat').read_text().split(') ', 1)[1].split()
    return dict(pid=int(pid), argv=args, proc_start_ticks=stat[19], state=stat[0],
                cwd=str((p / 'cwd').resolve()), executable=str((p / 'exe').resolve()))


def training_processes():
    rows = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            row = process(path.name)
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        if any(arg.endswith('/train.py') for arg in row['argv']):
            rows.append(row)
    return rows


def main():
    assert not (OUT / 'launch.json').exists(), 'Already launched: never create a second run'
    assert (OUT / 'cpu.passed').is_file() and (OUT / 'sim.passed').is_file()
    smoke = json.loads((OUT / 'smoke.json').read_text())
    assert smoke['status'] == 'PASS' and smoke['actor_input_dim'] == 695
    assert smoke['contract']['migration_revision'] == 3 and smoke['fusion_parameters'] == 0
    identity = json.loads((OUT / 'tested_source_identity.json').read_text())
    for relative, expected in identity.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
    rows = training_processes()
    stop = dict(checked_at=datetime.now().astimezone().isoformat(), processes_before=rows,
                signals_sent=[], status='NO_KICKBALL_PROCESS')
    candidates = []
    for row in rows:
        args = row['argv']
        assert '--task' in args, 'Unidentified training process'
        task = args[args.index('--task') + 1]
        assert 'kickball' in task.lower(), 'Other training is already running: ' + task
        assert row['cwd'] == str(ROOT) and 'ball/bin/python' in row['executable']
        candidates.append(row)
    for row in candidates:
        fresh = process(row['pid'])
        assert fresh['argv'] == row['argv'] and fresh['proc_start_ticks'] == row['proc_start_ticks']
        os.kill(row['pid'], signal.SIGINT)
        stop['signals_sent'].append(dict(pid=row['pid'], signal='SIGINT'))
        (OUT / 'stop_state.json').write_text(json.dumps(stop, ensure_ascii=False, indent=2) + '\n')
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                now = process(row['pid'])
            except (FileNotFoundError, ProcessLookupError):
                break
            if now['state'] == 'Z' or now['proc_start_ticks'] != row['proc_start_ticks']:
                break
            time.sleep(1)
        else:
            raise RuntimeError('Kickball did not exit after SIGINT; no escalation or wall13 launch')
    stop['status'] = 'KICKBALL_STOPPED' if candidates else 'NO_KICKBALL_PROCESS'
    (OUT / 'stop_state.json').write_text(json.dumps(stop, ensure_ascii=False, indent=2) + '\n')
    assert not training_processes(), 'Training process appeared before launch'
    free = int(subprocess.check_output(
        ['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).splitlines()[0])
    assert free >= 18000, f'Only {free} MiB free for formal training'
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name = 'wall13_24step_pose_concat9_fresh_' + stamp
    log = ROOT / 'logs/rsl_rl/g1_carrybox_depth/walled13' / ('train_' + name + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    command = ['bash', 'scripts/rsl_rl/train_carrybox_walled.sh', 'agent.num_steps_per_env=24',
               '--num_envs', '4096', '--max_iterations', '20000', '--seed', '42', '--run_name', name]
    env = os.environ.copy()
    env['CARRYBOX_VARIANT'] = '13'
    with log.open('xb') as stream:
        child = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                 stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    proc = process(child.pid)
    launched = dict(at=datetime.now().astimezone().isoformat(), pid=child.pid,
                    proc_start_ticks=proc['proc_start_ticks'], task=TASK, command=command,
                    run_name=name, stdout_log=str(log), free_mib_before=free, fresh=True,
                    migration_revision=3, actor_input_dim=695, num_envs=4096,
                    rollout_steps=24, max_iterations=20000, seed=42)
    # Write once: all subsequent health checks are read-only and cannot relaunch.
    with (OUT / 'launch.json').open('x') as stream:
        stream.write(json.dumps(launched, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(launched, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
