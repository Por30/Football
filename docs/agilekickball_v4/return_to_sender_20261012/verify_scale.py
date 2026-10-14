"""Validate the current bounded formal-launch run, not an arbitrary older checkpoint."""
import json
import re
from pathlib import Path
import torch
out = Path(__file__).parent
text = (out / 'scale.log').read_text()
assert 'Learning iteration 99/100' in text
assert 'return_to_sender_20261012' in text
assert not re.search(r'(?:loss|reward)\s*:\s*(?:nan|inf)\b', text, flags=re.I)
match = re.search(r'Exact experiment name requested from command line: (\S+)', text)
assert match, 'No exact run directory receipt'
run = Path('logs/rsl_rl/agilekickball_v4_smoke') / (match.group(1) + '_return_to_sender_scale_smoke')
checkpoint = run / 'model_99.pt'
state = torch.load(checkpoint, map_location='cpu', weights_only=False)
assert state['iter'] == 99
assert all(torch.isfinite(v).all() for v in state['model_state_dict'].values())
assert all(torch.isfinite(v).all() for v in state['amp_state_dict'].values())
assert state['initialization']['kind'] == 'v3_weights_only'
assert state['initialization']['source_iteration'] == 49999
course = state['agile_v4_return_curriculum']
assert course['config']['revision'] == 'return_to_sender_20261012'
assert course['return_direction']['steps'] >= 0
assert state['state_feedback']['aux_updates'] > 0
for metric in ('AgileKickball/recovered_serves', 'AgileV4/completed_rounds', 'AgileV4/foot_strike_rounds'):
    values = re.findall(re.escape(metric) + r':\s*([0-9.]+)', text)
    assert values and float(values[-1]) > 0, (metric, values[-3:])
result = dict(run=str(run), checkpoint=str(checkpoint), iterations=100, num_envs=4096,
              initialization=state['initialization'], curriculum=course,
              aux_updates=state['state_feedback']['aux_updates'], finite_policy_amp=True,
              recovery_completed_rounds_and_foot_contacts_positive=True)
(out / 'scale.json').write_text(json.dumps(result, indent=2) + '\n')
print('V4_SCALE_PASS', json.dumps(result))
