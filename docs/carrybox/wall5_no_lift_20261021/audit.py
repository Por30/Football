"""Snapshot recent completed iterations without modifying the live log."""
from pathlib import Path
from datetime import datetime
import json, re, statistics, hashlib
import torch

DOC = Path(__file__).resolve().parent
s = json.loads((DOC/'selection.json').read_text())
with open(s['training_log'], 'rb') as f:
    f.seek(0, 2)
    end = f.tell()
    start = max(0, end-4000000)
    f.seek(start)
    raw = f.read(end-start)
(DOC/'log_tail.txt').write_bytes(raw)
parts = re.split(r'Learning iteration\s+(\d+)/\d+', re.sub(r'\x1b\[[0-9;]*m', '', raw.decode(errors='replace')))
rows = []
for i in range(1, len(parts), 2):
    if 'Iteration time:' not in parts[i+1]:
        continue
    row = {'iteration': int(parts[i])}
    for line in parts[i+1].splitlines():
        m = re.match(r'\s*([^:]+):\s*(-?\d+(?:\.\d+)?)(?:s)?\s*$', line)
        if m:
            row[m[1].strip()] = float(m[2])
    rows.append(row)
assert len(rows) >= 250
window = rows[-250:]
means = {k: statistics.mean(r[k] for r in window) for k in window[-1] if all(k in r for r in window)}
means['amp_fraction_of_net_mixed_reward'] = means['Reward/amp_per_step']/means['Reward/mixed_per_step']
c = torch.load(s['checkpoint'], map_location='cpu', weights_only=False)
assert c['environment_contract']['reset_skill_probabilities'] == [.8, 0., .2]
assert c['environment_contract']['migration_revision'] == 19
assert all(torch.isfinite(v).all() for v in c['model_state_dict'].values())
result = dict(checked_at=datetime.now().astimezone().isoformat(), log=s['training_log'],
              log_byte_range=[start,end], log_tail_sha256=hashlib.sha256(raw).hexdigest(),
              latest=rows[-1], window_iterations=[window[0]['iteration'],window[-1]['iteration']],
              window_means=means, checkpoint=s['checkpoint'], contract=c['environment_contract'],
              note='Skill counters are cumulative rollout-averaged snapshots; episode reward combines loco and hold.')
(DOC/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
print('LOG_AUDIT_PASS', window[0]['iteration'], window[-1]['iteration'])
