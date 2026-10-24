"""Read-only launch verification; no simulator or GPU context is created."""
import json
import math
import re
from datetime import datetime
from pathlib import Path

import torch
import yaml

root = Path(__file__).resolve().parents[3]
docs = Path(__file__).resolve().parent
launch = json.loads((docs / 'launch.json').read_text())
proc = Path('/proc') / str(launch['pid'])
cmdline = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
assert launch['task'] in cmdline and 'agent.num_steps_per_env=24' in cmdline
assert proc.joinpath('stat').read_text().split(') ', 1)[1][0] != 'Z'
log_path = Path(launch['stdout_log'])
log = re.sub(r'\x1b\[[0-9;]*m', '', log_path.read_text(errors='replace'))
assert 'Traceback (most recent call last)' not in log
assert not re.search(r'(?<!\w)(?:nan|inf)(?!\w)', log, re.IGNORECASE)
iterations = [int(n) for n in re.findall(r'Learning iteration (\d+)/20000', log)]
times = [float(n) for n in re.findall(r'Iteration time:\s*([\d.]+)s', log)]
assert len(iterations) >= 12 and len(times) >= 12
assert iterations[:12] == list(range(12))
assert all(math.isfinite(t) and t > 0 for t in times)
runs = list(log_path.parent.glob('*_' + launch['run_name']))
assert len(runs) == 1
run = runs[0]
# IsaacLab emits Python tags in env.yaml; BaseLoader is sufficient for scalar checks.
agent = yaml.safe_load((run / 'params/agent.yaml').read_text())
env = yaml.load((run / 'params/env.yaml').read_text(), Loader=yaml.BaseLoader)
assert agent['num_steps_per_env'] == 24 and agent['max_iterations'] == 20000
assert agent['seed'] == 42 and agent['resume'] is False
assert agent['algorithm']['num_learning_epochs'] == 5
assert agent['algorithm']['num_mini_batches'] == 4
assert int(env['scene']['num_envs']) == 4096
model = run / 'model_0.pt'
state = torch.load(model, map_location='cpu', weights_only=False)
assert state['carrybox_schema'] == 2
assert state['amp']['config']['rollout_steps'] == 24
assert state['amp']['config']['schema'] == 10
for weights in (state['model_state_dict'], state['amp']['model']):
    assert weights and all(torch.isfinite(v).all().item() for v in weights.values())
optimizer = state['optimizer_state_dict']['state']
assert optimizer and all(float(s['step']) > 0 for s in optimizer.values())
assert list(run.glob('events.out.tfevents.*'))
summary = dict(checked_at=datetime.now().astimezone().isoformat(), pid=launch['pid'],
               run_dir=str(run), stdout_log=str(log_path), last_iteration=iterations[-1],
               num_envs=4096, num_steps_per_env=24, max_iterations=20000,
               mean_last10_seconds=sum(times[-10:]) / 10,
               max_last10_seconds=max(times[-10:]), model_0=str(model),
               checkpoint_schema=2, checkpoint_rollout_steps=24,
               policy_amp_finite=True, optimizer_updated=True, status='PASS')
(docs / 'health.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(summary, ensure_ascii=False, indent=2))
