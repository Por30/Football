"""Read-only formal startup acceptance; no claim about learned stability."""
from datetime import datetime
from pathlib import Path
import hashlib
import json
import re
import time
import torch

torch.set_num_threads(1)
DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
record = json.loads((DOC / 'launch.json').read_text())
assert record['initialization'] == 'fresh' and record['loaded_checkpoint'] is None
assert not any(a.startswith(('--resume', '--checkpoint', '--warm_start')) for a in record['command'])
start = time.monotonic()
first = None
while time.monotonic() - start < 900:
    command = [a.decode() for a in Path(f'/proc/{record["pid"]}/cmdline').read_bytes().split(b'\0') if a]
    assert command == record['command'], command
    log = Path(record['log']).read_text()
    assert not re.search(r'Traceback \(most recent call last\)|CUDA error:|out of memory|illegal memory access', log)
    iterations = [int(v) for v in re.findall(r'Learning iteration (\d+)/40000', log)]
    times = [float(v) for v in re.findall(r'Iteration time:\s*([\d.]+)s', log)]
    if iterations and first is None:
        first = iterations[-1]
    if len(times) >= 16 and iterations[-1] >= max(15, (first or 0) + 2):
        break
    print('WAIT', datetime.now().astimezone().isoformat(), iterations[-1] if iterations else 'startup', flush=True)
    time.sleep(15)
else:
    raise RuntimeError('Formal startup observation timed out')

runs = list((ROOT / 'logs/rsl_rl/g1_carrybox_depth/walled5').glob('*_' + record['run_name']))
assert len(runs) == 1, runs
run = runs[0]
model = torch.load(run / 'model_0.pt', map_location='cpu', weights_only=False)
c = model['environment_contract']
assert model['carrybox_schema'] == 2 and c['migration_revision'] == 15
assert c['roll_limit'] == .5 and c['roll_termination'] == 'abs_roll_gt_0.5'
assert c['reset_probs'] == [.8, 0., .2] and c['amp_shape'] == [10, 60]
assert c['actor_observations'] == 'proprio93x4_depth4x27x48_no_privileged' and c['critic_shape'] == 108
assert c['push_velocity_semantics'] == 'current_world_com_velocity_plus_curriculum_scaled_increment_v1'
for material in c['contact_materials'].values():
    assert material['static_friction'] == material['dynamic_friction'] == 1.
    assert material['friction_combine_mode'] == 'multiply'
assert c['reference_manifest_sha256'] == record['manifest_sha256']
state = model['model_state_dict']
for prefix, shape in [('critic.', (512, 108)), ('actor.', (512, 500))]:
    weights = [v for k, v in state.items() if k.startswith(prefix) and k.endswith('weight') and v.ndim == 2]
    assert tuple(weights[0].shape) == shape
for collection in (state, model['amp']['model']):
    assert all(torch.isfinite(v).all() for v in collection.values())
for optimizer in (model['optimizer_state_dict'], model['amp']['optimizer']):
    assert {int(v['step']) for v in optimizer['state'].values()} == {20}
    assert all(torch.isfinite(x).all() for v in optimizer['state'].values() for x in v.values() if isinstance(x, torch.Tensor))
assert model['amp']['dataset']['clip_count'] == 13 and model['amp']['config']['frame_dim'] == 60
count = int(model['amp']['model']['running_count'])
assert count == 61440, count
agent = (run / 'params/agent.yaml').read_text()
assert 'resume: false' in agent and 'class_name: CarryBoxWall5ActorCritic' in agent
environment = (run / 'params/env.yaml').read_text()
assert re.search(r'\bnum_envs:\s*4096\b', environment)
for name, expected in record['source_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
warm = times[-10:]
assert max(warm) <= 6., warm
metrics = {}
for key in ('Skill/loco_mean_steps', 'Skill/hold_mean_steps', 'Skill/loco_success_fraction',
            'Skill/hold_success_fraction', 'AMP/style_reward', 'Reward/amp_per_step', 'Mean episode length'):
    values = re.findall(re.escape(key) + r':\s*([-+\d.eE]+)', log)
    if values:
        metrics[key] = float(values[-1])
result = dict(status='PASS', checked_at=datetime.now().astimezone().isoformat(), pid=record['pid'],
    run=str(run), log=record['log'], checkpoint=str(run / 'model_0.pt'), initialization='fresh',
    progress_from=first, progress_to=iterations[-1], mean_iteration_seconds=sum(warm) / len(warm),
    max_iteration_seconds=max(warm), num_envs=4096, max_iterations=40000, seed=42,
    revision=15, roll_limit=.5, rsi=[.8, 0., .2], amp_clips=13, amp_frame_dim=60, critic_dim=108,
    initial_optimizer_steps=20, initial_amp_normalizer_count=count,
    finite_parameters_and_optimizers=True, source_unchanged=True, latest_logged_metrics=metrics,
    convergence_evaluated=False, previous_control_candidate_applied=False)
(DOC / 'snapshot.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2), flush=True)
