"""Start the user-requested fresh wall5 run once, preserving production code."""
from datetime import datetime
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import subprocess

DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
assert not (DOC / 'launch.json').exists(), 'Launch already recorded; verify it instead'
assert importlib.util.find_spec('isaacsim') is not None
assert all(t['result'] == 'PASS' for t in json.loads(
    (DOC.parent / 'wall5_distance3d_20261020/receipts.json').read_text())['tests'])
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():
        continue
    try:
        args = proc.joinpath('cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    assert not any(a.endswith((b'scripts/rsl_rl/train.py', b'scripts/rsl_rl/play.py')) for a in args), proc.name
free = int(subprocess.check_output(['nvidia-smi', '--query-gpu=memory.free',
    '--format=csv,noheader,nounits', '-i', '0'], text=True).strip())
assert free > 19000, free
assert shutil.disk_usage(ROOT).free > 30 * 1024**3
expected = json.loads((DOC.parent / 'wall5_distance3d_20261020/source_hashes.json').read_text())
for name, digest in expected.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
previous = json.loads((DOC.parent / 'wall5_reset_bug_20261019/launch.json').read_text())
paths = list(dict.fromkeys(list(previous['source_sha256']) + list(expected)))
paths += ['source/perceptual_ball/perceptual_ball/carrybox_wall5.py',
          'scripts/rsl_rl/train.py', 'scripts/rsl_rl/cli_args.py']
hashes = {}
for name in paths:
    data = (ROOT / name).read_bytes()
    hashes[name] = hashlib.sha256(data).hexdigest()
    target = DOC / 'source_snapshot' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
source = (ROOT / 'source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py').read_text()
assert "roll_termination='abs_roll_gt_0.5'" in source and 'roll_limit=.5' in source
assert 'migration_revision=18' in source and 'fixed_skill_ids' in source
dataset = ROOT / 'source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup'
manifest_bytes = (dataset / 'amp_manifest.json').read_bytes()
manifest = json.loads(manifest_bytes)
assert len(manifest['clips']) == 13
for clip in manifest['clips']:
    assert hashlib.sha256((dataset / clip['file']).read_bytes()).hexdigest() == clip['sha256'], clip['file']
name = 'wall5_v18_distance3d_fresh_' + datetime.now().strftime('%Y%m%d_%H%M%S')
log = ROOT / 'logs/rsl_rl/g1_carrybox_depth/walled5' / ('launch_' + name + '.log')
command = ['/home/cao/ENTER/envs/ball/bin/python', '-u', 'scripts/rsl_rl/train.py',
    '--task', 'Template-Perceptual-Ball-CarryBox-Walled5-v0', '--num_envs', '4096',
    '--device', 'cuda:0', '--headless', '--seed', '42', '--max_iterations', '40000', '--run_name', name]
with log.open('x') as stream:
    proc = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
        stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
record = dict(pid=proc.pid, command=command, log=str(log), run_name=name,
    initialization='fresh', loaded_checkpoint=None, started_at=datetime.now().astimezone().isoformat(),
    free_mib_before=free, source_sha256=hashes,
    dataset=str(dataset), manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
    user_authorization='Explicit stop current training and restart from scratch; revision18 XYZ distance, 4096 envs, no resume or warm-start')
(DOC / 'launch.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2), flush=True)
