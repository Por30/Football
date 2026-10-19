import json, hashlib, statistics
from pathlib import Path
p=Path(__file__).resolve().parent
selection=json.loads((p/'selection.json').read_text())
assert hashlib.sha256(Path(selection['checkpoint']).read_bytes()).hexdigest()==selection['checkpoint_sha256']
summary=json.loads((p/'baseline_summary.json').read_text())
for mode in ('mean','sample','reference'):
 d=json.loads((p/f'{mode}.json').read_text());rows=[f for ep in d['trajectories'] for f in ep]
 assert d['checkpoint_sha256']==selection['checkpoint_sha256'] and d['environment_contract_matched']
 assert len(d['first_episodes'])==32 and all(len(ep)==e['steps'] for ep,e in zip(d['trajectories'],d['first_episodes']))
 avg=sum(sum(f['reward_terms'].values()) for f in rows)/len(rows)*.02
 assert abs(avg-summary[mode]['task_per_step'])<1e-7
 if mode!='reference':assert all(e['tipped'] and not e['push_count'] for e in d['first_episodes'])
assert summary['sample']['task_per_step']<0 and summary['sample']['reward_per_step']['action_rate'] < -summary['sample']['reward_per_step']['walk_task']
print('BASELINE_AUDIT_PASS: primary records, reward dt, 64/64 policy tipped before push')
