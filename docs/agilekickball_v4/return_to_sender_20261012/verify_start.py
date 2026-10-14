"""Read-only verification after the formal process has completed early iterations."""
import json
import os
import re
from pathlib import Path
import torch
out = Path(__file__).parent
launch = json.loads((out / 'launch.json').read_text())
pid = launch['pid']
os.kill(pid, 0)
command = Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0', b' ').decode()
assert '--task Template-Perceptual-Ball-AgileKickball-v4 ' in command
assert '--warm_start_v3 ' in command
text = Path(launch['log']).read_text()
assert 'revision=return_to_sender_20261012' in text
assert '[INFO] v3 complete weights loaded' in text
assert 'Traceback (most recent call last)' not in text
iterations = re.findall(r'Learning iteration (\d+)/50000', text)
assert iterations and int(iterations[-1]) >= 10
name = re.search(r'Exact experiment name requested from command line: (\S+)', text).group(1)
run = Path('logs/rsl_rl/agilekickball_v4') / (name + '_return_to_sender_20261012_v3init')
initialization = json.loads((run / 'initialization.json').read_text())
assert initialization == launch['initialization']
checkpoint = run / 'model_0.pt'
state = torch.load(checkpoint, map_location='cpu', weights_only=False)
assert state['iter'] == 0 and state['initialization'] == initialization
assert all(torch.isfinite(v).all() for v in state['model_state_dict'].values())
assert all(torch.isfinite(v).all() for v in state['amp_state_dict'].values())
assert state['agile_v4_return_curriculum']['config']['revision'] == 'return_to_sender_20261012'
assert state['state_feedback']['aux_updates'] > 0
last_iteration_text = text[text.rfind('Learning iteration'):]
assert not re.search(r':\s*(?:nan|inf)\b', last_iteration_text, re.I)
metrics = {}
for metric in ('AgileKickball/recovered_serves', 'AgileV4/completed_rounds', 'AgileV4/foot_strike_rounds',
               'AgileV4/completed_target_hit_rate', 'AgileV4/completed_strict_20cm_hit_rate',
               'AgileV4/target_half_width_m', 'AgileV4/speed_upper_m_s'):
    values = re.findall(re.escape(metric) + r':\s*([0-9.]+)', text)
    assert values, metric
    metrics[metric] = float(values[-1])
for metric in ('AgileKickball/recovered_serves', 'AgileV4/completed_rounds', 'AgileV4/foot_strike_rounds'):
    assert metrics[metric] > 0
result = dict(pid=pid, pid_alive=True, command=command, log=launch['log'],
              run=str(run), checkpoint=str(checkpoint), last_iteration=int(iterations[-1]),
              finite_checkpoint=True, initialization=initialization,
              console_last_iteration_averaged_metrics=metrics)
(out / 'verified_start.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
