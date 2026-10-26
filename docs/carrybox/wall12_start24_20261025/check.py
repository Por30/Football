"""Read-only verification of the actual formal wall12 launch; no GPU context."""
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

import torch
import yaml

docs = Path(__file__).resolve().parent
if not (docs / 'launch.json').exists():
    print('BLOCKED: wall12尚未启动；等待用户选择如何处理足球训练占用的GPU。', file=sys.stderr)
    raise SystemExit(2)
launch = json.loads((docs / 'launch.json').read_text())
proc = Path('/proc') / str(launch['pid'])
cmdline = proc.joinpath('cmdline').read_bytes().replace(b'\0', b' ').decode()
assert launch['task'] in cmdline and 'agent.num_steps_per_env=24' in cmdline
assert '--resume' not in cmdline and '--warm_start_carrybox' not in cmdline
assert proc.joinpath('stat').read_text().split(') ', 1)[1][0] != 'Z'
log_path = Path(launch['stdout_log'])
log = re.sub(r'\x1b\[[0-9;]*m', '', log_path.read_text(errors='replace'))
assert 'Traceback (most recent call last)' not in log
assert not re.search(r'(?<!\w)(?:nan|inf)(?!\w)', log, re.IGNORECASE)
assert 'PhysX error' not in log and 'CUDA error:' not in log and 'out of memory' not in log.lower()
iterations = [int(n) for n in re.findall(r'Learning iteration (\d+)/20000', log)]
times = [float(n) for n in re.findall(r'Iteration time:\s*([\d.]+)s', log)]
assert len(iterations) >= 12 and len(times) >= 12
assert iterations[:12] == list(range(12))
assert all(math.isfinite(t) and t > 0 for t in times)
runs = list(log_path.parent.glob('*_' + launch['run_name']))
assert len(runs) == 1
run = runs[0]
agent = yaml.safe_load((run / 'params/agent.yaml').read_text())
env = yaml.load((run / 'params/env.yaml').read_text(), Loader=yaml.BaseLoader)
assert agent['num_steps_per_env'] == 24 and agent['max_iterations'] == 20000
assert agent['seed'] == 42 and agent['resume'] is False
assert agent['algorithm']['num_learning_epochs'] == 5
assert agent['algorithm']['num_mini_batches'] == 4
assert agent['algorithm']['pose_aux_coef'] == 1.
assert agent['algorithm']['class_name'] == 'CarryBoxWall12PPO'
assert env['walled_variant'] == 'walled12'
assert int(env['scene']['num_envs']) == 4096
assert float(env['depth_noise']['gaussian_std']) == .02
assert all(env['scene'][f'cylinder{i}'] is not None for i in range(3))
model = run / 'model_0.pt'
state = torch.load(model, map_location='cpu', weights_only=False)
assert state['carrybox_schema'] == 2 and state['pose_aux_coef'] == 1.
contract = state['environment_contract']
assert contract['variant'] == 'walled12' and contract['migration_revision'] == 1
assert contract['actor'] == 'proprio93x6_depth4x27x48'
aux = contract['pose_supervision']
assert aux['frame'] == 'camera_optical_xright_ydown_zforward'
assert aux['prediction_dim'] == 9 and aux['target_dim'] == 12
assert aux['actor_feedback'] is False
assert contract['obstacles']['cylinder_count'] == 3
assert contract['obstacles']['collision'] and contract['obstacles']['depth_occlusion']
amp = state['amp']['config']
assert amp['rollout_steps'] == 24 and amp['schema'] == 12
assert amp['auxiliary'] == dict(aux, coef=1.)
assert 'Wall12/' in log
for weights in (state['model_state_dict'], state['amp']['model']):
    assert weights and all(torch.isfinite(v).all().item() for v in weights.values())
optimizer = state['optimizer_state_dict']
assert len(optimizer['param_groups']) == 3
assert optimizer['state'] and all(float(s['step']) == 20 for s in optimizer['state'].values())
# Wall12 appends the four pose-head tensors to the original policy Adam group.
head_names = [name for name in state['model_state_dict'] if name.startswith('pose_head.')]
assert len(head_names) == 4
head_ids = optimizer['param_groups'][0]['params'][-4:]
for name, parameter_id in zip(head_names, head_ids):
    saved = optimizer['state'][parameter_id]
    assert saved['exp_avg'].shape == state['model_state_dict'][name].shape
    assert torch.isfinite(saved['exp_avg']).all() and torch.isfinite(saved['exp_avg_sq']).all()
    assert torch.count_nonzero(saved['exp_avg']).item() > 0
assert list(run.glob('events.out.tfevents.*'))
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
events = EventAccumulator(str(run), size_guidance={'scalars': 0})
events.Reload()
scalars = {}
for tag in ('Loss/pose_position', 'Loss/pose_rotation', 'Loss/pose_aux_weighted', 'Loss/pose_samples'):
    values = events.Scalars(tag)
    assert values and all(math.isfinite(value.value) for value in values)
    scalars[tag] = values[-1].value
assert scalars['Loss/pose_samples'] == 4096 * 23 * 5
summary = dict(checked_at=datetime.now().astimezone().isoformat(), pid=launch['pid'],
    run_dir=str(run), stdout_log=str(log_path), last_iteration=iterations[-1],
    num_envs=4096, num_steps_per_env=24, max_iterations=20000, seed=42,
    mean_last10_seconds=sum(times[-10:]) / 10, max_last10_seconds=max(times[-10:]),
    model_0=str(model), checkpoint_schema=2, variant='walled12',
    fresh_start=True, aux=aux, auxiliary_scalars=scalars, policy_amp_finite=True,
    pose_adam_moments_nonzero=True, optimizer_step=20, status='PASS')
(docs / 'health.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(summary, ensure_ascii=False, indent=2))
