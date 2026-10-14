#!/usr/bin/env python3
"""One-shot local queue: completed football -> bounded wall4 preflight -> training.

No imports from the simulator; the supervisor survives the interactive session.
Never adopts, stops or restarts an existing training process.
"""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / 'logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013'
FATAL = re.compile(r'Traceback \(most recent call last\)|illegal memory access|CUDA error:|Synchronizing GPU Narrowphase failed|fail to launch.*kernel|convexCoreConvexNphase_Kernel fail|PhysX error|out of memory', re.I)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    with temp.open('w') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, path)


def identity(pid, proc=Path('/proc')):
    try:
        directory = proc / str(pid)
        stat = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
        if stat[0] == 'Z':
            return None
        return dict(pid=int(pid), start_ticks=int(stat[19]),
                    boot_id=(proc / 'sys/kernel/random/boot_id').read_text().strip(),
                    cwd=str((directory / 'cwd').resolve(strict=True)),
                    argv=(directory / 'cmdline').read_bytes().decode().strip('\0').split('\0'))
    except (FileNotFoundError, ProcessLookupError):
        return None


def training_processes():
    found = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            current = identity(int(entry.name))
        except (PermissionError, OSError):
            continue
        if current and any(Path(a).name in ('train.py', 'smoke_carrybox_walled.py') for a in current['argv']):
            found.append(current)
    return found


def source_hashes():
    paths = set((ROOT / 'source/perceptual_ball').rglob('*.py'))
    paths.update(ROOT / p for p in ('scripts/rsl_rl/train.py', 'scripts/rsl_rl/train_carrybox_walled.sh',
        'scripts/rsl_rl/queue_wall4.py', 'scripts/rsl_rl/smoke_carrybox_walled.py',
        'scripts/rsl_rl/smoke_carrybox_walled.sh', 'scripts/rsl_rl/validate_carrybox_runtime.sh', 'findbox/amp_manifest.json'))
    paths.update((ROOT / 'findbox').rglob('*.pt'))
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}


def verify_hashes(expected):
    actual = source_hashes()
    changed = sorted(k for k in actual.keys() | expected.keys() if actual.get(k) != expected.get(k))
    if changed:
        raise ValueError('Source/data changed after queue registration: ' + ', '.join(changed))


def load_checkpoint(path, expected_iter, football=True):
    import torch
    state = torch.load(path, map_location='cpu', weights_only=False)
    if state.get('iter') != expected_iter:
        raise ValueError(f'Checkpoint iteration {state.get("iter")} != {expected_iter}')
    if not state.get('model_state_dict') or not state.get('optimizer_state_dict'):
        raise ValueError('Missing policy/optimizer state')
    if football:
        revision = state.get('agile_v4_return_curriculum', {}).get('config', {}).get('revision')
        if state.get('soccer_schema_version') != 3 or revision != 'return_to_sender_20261012':
            raise ValueError('Wrong football task/checkpoint revision')
    elif state.get('environment_contract', {}).get('variant') != 'walled4':
        raise ValueError('Wrong wall4 checkpoint variant')
    count = 0
    def finite(value):
        nonlocal count
        if torch.is_tensor(value):
            count += 1
            if (value.is_floating_point() or value.is_complex()) and not torch.isfinite(value).all():
                raise ValueError('Nonfinite checkpoint tensor')
        elif isinstance(value, dict):
            for item in value.values(): finite(item)
        elif isinstance(value, (tuple, list)):
            for item in value: finite(item)
    finite(state)
    return dict(path=str(path), iteration=expected_iter, tensor_count=count, sha256=sha(path))


def verify_completion(log_path, model_path, final_iter, total, football=True):
    log = Path(log_path).read_text(errors='replace')
    if not re.search(rf'Learning iteration\s+{final_iter}/{total}\b', log):
        raise ValueError('Final learning iteration is absent from log')
    fatal = FATAL.search(log)
    if fatal:
        raise ValueError('Fatal training log evidence: ' + fatal.group())
    path = Path(model_path)
    st = path.stat()
    if st.st_size == 0 or time.time() - st.st_mtime < 10:
        raise ValueError('Final checkpoint is empty or not yet stable')
    evidence = load_checkpoint(path, final_iter, football)
    if (path.stat().st_size, path.stat().st_mtime_ns) != (st.st_size, st.st_mtime_ns):
        raise ValueError('Checkpoint changed during validation')
    return evidence


def verify_smokes():
    evidence = {}
    for variant in (3, 4):
        directory = ROOT / f'docs/carrybox/wall4_repair/walled{variant}'
        report = json.loads((directory / 'smoke.json').read_text())
        log = (directory / 'smoke.log').read_text(errors='replace')
        if (report.get('status') != 'PASS' or report.get('iterations', 0) < 20
                or report.get('num_envs') != 4 or report.get('resumed_iterations', 0) < 2 or report.get('resets', 0) == 0 or 'CARRYBOX_WALLED_SMOKE_PASS' not in log or FATAL.search(log)):
            raise ValueError(f'Wall{variant} training smoke is not ready')
        geometry = json.loads((directory / 'geometry.json').read_text())
        geometry_log = (directory / 'geometry.log').read_text(errors='replace')
        if (geometry.get('status') != 'PASS' or not geometry.get('collision_checks')
                or not geometry.get('depth_changes') or FATAL.search(geometry_log)
                or 'CARRYBOX_WALLED_SMOKE_PASS' not in geometry_log):
            raise ValueError(f'Wall{variant} geometry smoke is not ready')
        evidence[str(variant)] = {name: sha(directory / name) for name in
                                 ('smoke.json', 'smoke.log', 'geometry.json', 'geometry.log')}
    return evidence


def gpu_status():
    out = subprocess.check_output(['nvidia-smi', '--id=0', '--query-gpu=uuid,memory.free,memory.used',
                                   '--format=csv,noheader,nounits'], text=True, timeout=15)
    uuid, free, used = [s.strip() for s in out.strip().split(',')]
    return dict(uuid=uuid, free_mib=int(free), used_mib=int(used))


def acquire_lock(path):
    handle = Path(path).open('a')
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BaseException:
        handle.close(); raise
    return handle


class Queue:
    def __init__(self, directory):
        self.directory = directory
        self.config = json.loads((directory / 'config.json').read_text())
        self.state = dict(queue_id=self.config['queue_id'], supervisor=identity(os.getpid()))

    def record(self, status, **fields):
        self.state.update(status=status, updated_utc=datetime.now(timezone.utc).isoformat(), **fields)
        atomic_json(self.directory / 'status.json', self.state)
        print(self.state['updated_utc'], status, fields.get('reason', ''), flush=True)

    def resources(self, minimum):
        gpu = gpu_status()
        if gpu['uuid'] != self.config['gpu_uuid']:
            raise ValueError('GPU identity changed')
        others = training_processes()
        if others or gpu['free_mib'] < minimum:
            self.record('WAITING_RESOURCES', gpu=gpu, other_training=others, required_free_mib=minimum)
            return False
        return True

    def preflight(self):
        # Fresh process, full 128 environments, default PPO epochs and 20 s episodes.
        output = ROOT / 'docs/carrybox/wall4_repair/queue_confirm/scale128'
        output.mkdir(parents=True, exist_ok=True)
        if (output / 'smoke.json').exists():
            raise ValueError('Preflight output already exists; refusing ambiguous reuse')
        env = os.environ.copy()
        env.update(WALLED_VARIANTS='4', WALLED_SCALE_PREFLIGHT='1',
                   WALLED_OUTPUT_ROOT=str(output.parent))
        before = gpu_status()
        peak = before['used_mib']
        self.record('PREFLIGHT', output=str(output))
        with (self.directory / 'preflight.log').open('w') as log:
            child = subprocess.Popen(['bash', 'scripts/rsl_rl/smoke_carrybox_walled.sh'], cwd=ROOT,
                                     env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            deadline = time.monotonic() + 1260
            while child.poll() is None:
                peak = max(peak, gpu_status()['used_mib'])
                self.record('PREFLIGHT', child=identity(child.pid), peak_gpu_used_mib=peak)
                if time.monotonic() > deadline:
                    os.killpg(child.pid, signal.SIGKILL); child.wait()
                    raise ValueError('128-environment preflight timed out; no training launched')
                time.sleep(5)
        report = json.loads((output / 'smoke.json').read_text())
        contents = (output / 'smoke.log').read_text(errors='replace')
        if (child.returncode or report.get('status') != 'PASS' or report.get('num_envs') != 128
                or not report.get('scale_preflight') or report.get('iterations', 0) < 50
                or 'CARRYBOX_WALLED_SMOKE_PASS' not in contents or FATAL.search(contents)):
            raise ValueError('128-environment preflight failed')
        evidence = dict(report=report, report_sha256=sha(output / 'smoke.json'),
                        peak_gpu_used_mib=peak, baseline_gpu_used_mib=before['used_mib'],
                        required_free_mib=peak-before['used_mib']+2048)
        atomic_json(self.directory / 'preflight_receipt.json', evidence)
        return evidence

    def run(self):
        with acquire_lock(self.directory / 'queue.lock'):
            # A previous launch intent requires manual reconciliation, never blind retry.
            if (self.directory / 'launch_intent.json').exists():
                raise ValueError('Launch intent already exists: automatic relaunch is forbidden')
            expected = self.config['football_identity']
            if expected['boot_id'] != Path('/proc/sys/kernel/random/boot_id').read_text().strip():
                raise ValueError('Host rebooted since registration; football exit cannot be inferred')
            while True:
                actual = identity(expected['pid'])
                if actual is None:
                    break
                if actual != expected:
                    raise ValueError('Football PID identity changed')
                self.record('WAITING_FOOTBALL', football_pid=expected['pid'])
                time.sleep(60)
            time.sleep(15)  # final checkpoint close/mtime stability, after process exit
            self.record('VERIFYING_FOOTBALL')
            complete = verify_completion(self.config['football_log'], self.config['football_checkpoint'], 49999, 50000)
            self.record('VERIFYING_WALL4', football_completion=complete)
            verify_hashes(self.config['source_hashes'])
            if verify_smokes() != self.config['smoke_evidence']:
                raise ValueError('Readiness smoke evidence changed')
            while not self.resources(20000): time.sleep(60)
            preflight = self.preflight()
            while not self.resources(preflight['required_free_mib']): time.sleep(60)
            verify_hashes(self.config['source_hashes'])
            if verify_smokes() != self.config['smoke_evidence']:
                raise ValueError('Readiness evidence changed during preflight')
            command = self.config['train_command']
            intent = dict(command=command, cwd=str(ROOT), preflight=preflight,
                          queue_id=self.config['queue_id'], utc=datetime.now(timezone.utc).isoformat())
            atomic_json(self.directory / 'launch_intent.json', intent)
            self.record('STARTING', command=command)
            train_log = self.directory / 'train.log'
            with train_log.open('x') as log:
                child = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log,
                                         stderr=subprocess.STDOUT, start_new_session=True)
            self.record('STARTING', child=identity(child.pid), train_log=str(train_log))
            deadline = time.monotonic() + 900
            while child.poll() is None:
                contents = train_log.read_text(errors='replace')
                if 'Learning iteration 0/40000' in contents:
                    self.record('RUNNING', child=identity(child.pid))
                    break
                if FATAL.search(contents) or time.monotonic() > deadline:
                    # Kill only the process group launched by this supervisor.
                    os.killpg(child.pid, signal.SIGKILL); child.wait()
                    raise ValueError('Wall4 startup failed/hung; see train.log (no automatic restart)')
                time.sleep(10)
            while child.poll() is None:
                contents = train_log.read_text(errors='replace')
                if FATAL.search(contents):
                    os.killpg(child.pid, signal.SIGKILL); child.wait()
                    raise ValueError('Wall4 fatal training error; stopped its own failed process group')
                self.record('RUNNING', child=identity(child.pid)); time.sleep(60)
            time.sleep(15)
            candidates = list((ROOT / 'logs/rsl_rl/g1_carrybox_depth/walled4').glob('*_' + self.config['run_name'] + '/model_39999.pt'))
            if child.returncode or len(candidates) != 1:
                raise ValueError(f'Wall4 exited without a unique final checkpoint, exit={child.returncode}')
            complete = verify_completion(train_log, candidates[0], 39999, 40000, football=False)
            self.record('COMPLETED', wall4_completion=complete, exit_code=child.returncode)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=DEFAULT)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    if args.check_only:
        evidence = verify_smokes()
        assert ROOT.is_dir() and (ROOT / 'scripts/rsl_rl/train_carrybox_walled.sh').is_file()
        print(json.dumps({'status': 'PASS', 'smokes': evidence, 'source_files': len(source_hashes())}))
        return 0
    queue = Queue(args.directory)
    try:
        queue.run()
    except BlockingIOError:
        print('Another queue supervisor holds the lock; no action taken.', flush=True)
        return 2
    except BaseException as exc:
        queue.record('BLOCKED', reason=f'{type(exc).__name__}: {exc}')
        raise
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
