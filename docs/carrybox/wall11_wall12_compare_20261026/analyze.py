import hashlib
import json
from pathlib import Path
import numpy as np
import torch
import yaml
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

OUT = Path(__file__).resolve().parent
RUNS = {
    11: 'logs/rsl_rl/g1_carrybox_depth/walled11/2026-10-24_12-34-49_wall11_24step_fresh_20261024_123445',
    12: 'logs/rsl_rl/g1_carrybox_depth/walled12/2026-10-25_12-32-53_wall12_24step_pose_aux_fresh_20261025_123249',
}


def differences(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        return [p for k in a.keys() | b.keys() for p in differences(a.get(k), b.get(k), path+'.'+k)]
    return [] if a == b else [path.lstrip('.')]


torch.set_num_threads(1)
states, agents, records, arrays = {}, {}, {}, {}
for v, name in RUNS.items():
    run = Path(name)
    model = run/'model_19999.pt'
    state = torch.load(model, weights_only=False, map_location='cpu')
    assert state['iter'] == 19999 and state['carrybox_schema'] == 2
    assert state['pose_aux_coef'] == (0. if v == 11 else 1.)
    assert all(torch.isfinite(t).all() for t in state['model_state_dict'].values())
    states[v] = state
    agents[v] = yaml.safe_load((run/'params/agent.yaml').read_text())
    events = EventAccumulator(str(run), size_guidance={'scalars': 0}).Reload()
    stats = {}
    for tag in events.Tags()['scalars']:
        if tag.endswith('/time'):
            continue
        rows = events.Scalars(tag)
        assert [r.step for r in rows] == list(range(20000)), (v, tag)
        values = np.array([r.value for r in rows])
        assert np.isfinite(values).all(), tag
        canonical = tag.replace(f'Wall{v}/', 'Task/')
        arrays[f'wall{v}::{canonical}'] = values
        stats[canonical] = dict(last=float(values[-1]), last1000=float(values[-1000:].mean()),
            blocks={str(i):float(values[i:i+1000].mean()) for i in range(0,20000,1000)})
    records[str(v)] = dict(run=name, checkpoint=str(model),
        checkpoint_sha256=hashlib.sha256(model.read_bytes()).hexdigest(), seed=agents[v]['seed'],
        iterations=20000, aux_coef=state['pose_aux_coef'], stats=stats)

env_diff = differences(states[11]['environment_contract'], states[12]['environment_contract'])
assert set(env_diff) == {'variant','parent','pose_supervision'}, env_diff
agent_diff = differences(agents[11], agents[12])
assert set(agent_diff) == {'class_name','experiment_name','run_name','algorithm.class_name','algorithm.pose_aux_coef'}, agent_diff
amp_diff = differences(states[11]['amp']['config'], states[12]['amp']['config'])
assert set(amp_diff) == {'schema','auxiliary'}, amp_diff
assert states[11]['amp']['dataset'] == states[12]['amp']['dataset']
assert states[11]['model_state_dict'].keys() == states[12]['model_state_dict'].keys()
assert all(states[11]['model_state_dict'][k].shape == v.shape for k,v in states[12]['model_state_dict'].items())
result = dict(status='PASS', runs=records, environment_contract_differences=env_diff,
    agent_differences=agent_diff, amp_config_differences=amp_diff, identical_amp_data=True,
    training_seeds_per_condition=1, cumulative_success_note='Task/*success_fraction is cumulative since process start, not current policy success.')
(OUT/'training.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
np.savez_compressed(OUT/'curves.npz', **arrays)
print(json.dumps({k:{t:r['stats'][t] for t in ('Train/mean_reward','Train/mean_episode_length',
    'Task/hold_fraction','Task/ground_start_success_fraction')} for k,r in records.items()},indent=2))
print('ANALYSIS_PASS', flush=True)
