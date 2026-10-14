"""Read-only acceptance of the explicitly requested 4096-environment run."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import torch

out = Path(__file__).resolve().parent
root = out.parents[2]
state = json.loads((out / 'launch.json').read_text())
proc = Path('/proc') / str(state['pid'])
assert proc.joinpath('stat').read_text().rsplit(')', 1)[1].split()[19] == state['start_ticks']
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip() == state['boot_id']
assert not Path('/proc/2322385').exists(), 'Old 128-env worker still exists'
log = Path(state['train_log']).read_text(errors='replace')
assert 'Number of environments: 4096' in log
for error in ('Traceback (most recent call last)', 'CUDA out of memory', 'CUDA error:', 'cudaErrorIllegalAddress', 'Non-finite CarryBox'):
    assert error not in log, error
run = next((root / 'logs/rsl_rl/g1_carrybox_depth/walled4').glob('*_' + state['run_name']))
assert re.search(r'num_envs:\s*4096\b', (run / 'params/env.yaml').read_text())
chunks = re.split(r'Learning iteration\s+(\d+)/40000', log)
rows = []
for i in range(1, len(chunks), 2):
    row = {'iteration': int(chunks[i])}
    for line in chunks[i + 1].splitlines():
        match = re.match(r'\s*([^:]+):\s*(-?\d+(?:\.\d+)?)\s*$', line)
        if match:
            row[match[1].strip()] = float(match[2])
    if 'Total timesteps' in row and 'Mean episode length' in row:
        rows.append(row)
assert len(rows) >= 2
assert rows[-1]['Total timesteps'] == (rows[-1]['iteration'] + 1) * 4096 * 24
assert rows[-1]['Mean amp_valid_samples loss'] > 0
checkpoint = run / 'model_0.pt'
ck = torch.load(checkpoint, map_location='cpu', weights_only=False)
assert ck['carrybox_schema'] == 2
assert ck['environment_contract']['migration_revision'] == 4
assert ck['environment_contract']['failure_reward'] == 'current_transition'
assert all(torch.isfinite(v).all() for v in ck['model_state_dict'].values() if torch.is_tensor(v))
manifest = root / 'findbox/amp_manifest.json'
assert ck['amp']['dataset']['manifest_sha256'] == hashlib.sha256(manifest.read_bytes()).hexdigest()
keys = ('iteration', 'Mean episode length', 'Mean reward', 'Mean amp_valid_samples loss', 'AMP/valid_fraction', 'Episode_Reward/fall', 'Metrics/episode_lift_success')
result = dict(status='PASS', checked_local=datetime.datetime.now().astimezone().isoformat(), pid=state['pid'], num_envs=4096,
              run_directory=str(run), checkpoint=str(checkpoint), checkpoint_finite=True,
              last_complete_iteration=rows[-1]['iteration'], latest_metrics={k: rows[-1].get(k) for k in keys},
              conclusion='Startup and initial training updates verified; convergence not established')
(out / 'health.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
