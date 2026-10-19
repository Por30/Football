"""Pin completed weights and audit recent per-skill training counters read-only."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import re
import statistics as st
import torch

torch.set_num_threads(1)
DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
s = json.loads((DOC / 'selection.json').read_text())
checkpoint = Path(s['checkpoint'])
assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == s['checkpoint_sha256']
model = torch.load(checkpoint, map_location='cpu', weights_only=False)
c = model['environment_contract']
assert model['iter'] == s['checkpoint_iteration']
assert c['migration_revision'] == 15 and c['roll_limit'] == .5
assert c['roll_termination'] == 'abs_roll_gt_0.5' and c['critic_shape'] == 108
assert c['reset_probs'] == [.8, 0., .2] and c['amp_shape'] == [10, 60]
assert c['actor_observations'] == 'proprio93x4_depth4x27x48_no_privileged'
assert c['reference_manifest_sha256'] == s['manifest_sha256']
assert model['amp']['dataset']['clip_count'] == 13
assert all(torch.isfinite(v).all() for v in model['model_state_dict'].values())
for name, digest in s['source_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
command = [a.decode() for a in Path(f'/proc/{s["training_pid"]}/cmdline').read_bytes().split(b'\0') if a]
assert command == s['training_command']
raw = Path(s['log']).read_bytes()
pieces = re.split(r'Learning iteration\s+(\d+)/\d+', re.sub(r'\x1b\[[0-9;]*m', '', raw.decode(errors='replace')))
rows = []
for i in range(1, len(pieces), 2):
    if 'Iteration time:' not in pieces[i+1]:
        continue
    row = {'iteration': int(pieces[i])}
    for line in pieces[i+1].splitlines():
        m = re.fullmatch(r'\s*([^:]+):\s*(-?\d+(?:\.\d+)?)(?:s)?\s*', line)
        if m:
            row[m[1].strip()] = float(m[2])
    rows.append(row)
assert len(rows) > 250
a, b = rows[-251], rows[-1]
skills = {}
for skill in ('loco', 'hold'):
    prefix = 'Skill/' + skill + '_'
    episodes = b[prefix+'episodes'] - a[prefix+'episodes']
    steps = b[prefix+'valid_amp_steps'] - a[prefix+'valid_amp_steps']
    assert episodes > 0 and steps > 0
    skills[skill] = dict(completed_episodes_approx=episodes, completed_steps_approx=steps,
        mean_steps_approx=steps/episodes, mean_seconds_approx=.02*steps/episodes,
        success_delta_approx=b[prefix+'successes']-a[prefix+'successes'])
total = sum(v['completed_steps_approx'] for v in skills.values())
for v in skills.values():
    v['completed_step_fraction_approx'] = v['completed_steps_approx']/total
keys = ['Mean episode length', 'Control/physical_target_clipped_fraction', 'Reward/task_weighted_per_step',
        'Reward/amp_per_step', 'Mean box_position loss', 'Iteration time',
        'Episode_Termination/time_out', 'Episode_Termination/tipped', 'Episode_Termination/fell']
audit = dict(status='PASS', checked_at=datetime.now().astimezone().isoformat(),
    checkpoint=s['checkpoint'], checkpoint_sha256=s['checkpoint_sha256'],
    checkpoint_iteration=s['checkpoint_iteration'], environment_contract=c,
    log_snapshot_sha256=hashlib.sha256(raw).hexdigest(), first_recent=rows[-250]['iteration'],
    last_iteration=b['iteration'], recent_means={k:st.mean(row[k] for row in rows[-250:]) for k in keys},
    skill_window=skills, policy_std=model['model_state_dict']['log_std'].exp().tolist(),
    training_pid=s['training_pid'], training_command_matches=True,
    limits=['Per-skill deltas use rounded rollout-averaged cumulative logs: approximate completed-episode steps, not exact buffer allocation',
            'Concurrent training can advance beyond the pinned checkpoint; this audit is timestamped'])
(DOC / 'training_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
print(json.dumps({k:v for k,v in audit.items() if k not in ('environment_contract','policy_std')}, indent=2))
