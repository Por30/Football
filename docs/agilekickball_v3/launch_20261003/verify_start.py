"""Read-only validation of the specifically authorized detached v3 run."""
import json
import os
from pathlib import Path
import re
import torch
import yaml

root = Path(__file__).resolve().parents[3]
out = Path(__file__).resolve().parent
meta = json.loads((out / 'launch.json').read_text())
pid = meta['pid']
proc = Path('/proc') / str(pid)
args = proc.joinpath('cmdline').read_bytes().split(b'\0')
assert b'scripts/rsl_rl/train.py' in args and b'Template-Perceptual-Ball-AgileKickball-v3' in args
stat = proc.joinpath('stat').read_text().split(') ', 1)[1].split()
assert int(stat[19]) == meta['start_ticks'], 'PID has been reused'
assert os.getsid(pid) == pid, 'Training must be in an independent session'
log = Path(meta['log']).read_text(errors='replace')
assert 'Traceback (most recent call last)' not in log
assert 'CUDA out of memory' not in log
iterations = re.findall(r'Learning iteration\s+(\d+)/(\d+)', log)
assert iterations and int(iterations[-1][0]) >= 2 and int(iterations[-1][1]) == 50000
match = re.search(r'Exact experiment name requested from command line: (\S+)', log)
assert match
run = root / 'logs/rsl_rl/agilekickball_v3' / (match.group(1) + '_contact_outcome_20261003_scratch')
agent = yaml.safe_load((run / 'params/agent.yaml').read_text())
assert (agent['max_iterations'], agent['seed'], agent['resume']) == (50000, 42, False)
assert agent['num_steps_per_env'] == 24 and agent['experiment_name'] == 'agilekickball_v3'
assert agent['policy']['class_name'] == 'OutcomeActorCritic'
assert agent['algorithm']['class_name'] == 'ContactOutcomePPO'
assert agent['algorithm']['outcome_aux_coef'] == .1 and agent['algorithm']['outcome_horizon'] == 8
assert '--num_envs' in [a.decode() for a in args]
assert args[args.index(b'--num_envs') + 1] == b'4096'
assert args[args.index(b'--device') + 1] == b'cuda:0'
checkpoint = run / 'model_0.pt'
state = torch.load(checkpoint, weights_only=False, map_location='cpu')
assert state['soccer_schema_version'] == 3
assert all(torch.isfinite(v).all() for v in state['model_state_dict'].values())
course = state['agile_v3_wide_serve_curriculum']
assert course['schema'] == 5 and course['config']['revision'] == 'contact_outcome_20261003'
assert state['contact_outcome']['config']['coef'] == .1
assert state['contact_outcome']['optimizer']['state']
assert any('outcome_head' in key for key in state['model_state_dict'])
report = dict(pid=pid, independent_session=True, num_envs=4096, max_iterations=50000,
              seed=42, resume=False, revision=course['config']['revision'],
              latest_iteration_at_check=int(iterations[-1][0]),
              run_dir=str(run), log=meta['log'], first_checkpoint=str(checkpoint),
              finite_first_checkpoint=True, outcome_optimizer_present=True)
(out / 'verified_start.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
