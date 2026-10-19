from pathlib import Path
import json,re,hashlib,statistics as st
import torch
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2]
ckpt=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_00-37-11_wall5_v14_asymmetric_fresh_20261019_003706/model_11200.pt'
x=torch.load(ckpt,map_location='cpu',weights_only=False)
assert x['iter']==11200 and x['environment_contract']['migration_revision']==14
assert x['environment_contract']['reset_skill_probabilities']==[.8,0.,.2]
assert all(torch.isfinite(v).all() for v in x['model_state_dict'].values())
prev=json.loads((ROOT/'docs/carrybox/wall5_play11000_20261019/recording.json').read_text())
assert json.loads(json.dumps(x['environment_contract']))==prev['environment_contract']
for path,digest in prev['archived_sources'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
log=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v14_asymmetric_fresh_20261019_003706.log'
raw=log.read_bytes();pieces=re.split(r'Learning iteration\s+(\d+)/\d+',re.sub(r'\x1b\[[0-9;]*m','',raw.decode(errors='replace')));rows=[]
for i in range(1,len(pieces),2):
 if 'Iteration time:' not in pieces[i+1]:continue
 row=dict(iteration=int(pieces[i]))
 for line in pieces[i+1].splitlines():
  m=re.fullmatch(r'\s*([^:]+):\s*(-?\d+(?:\.\d+)?)(?:s)?\s*',line)
  if m:row[m[1].strip()]=float(m[2])
 rows.append(row)
a,b=rows[-251],rows[-1];skills={}
for skill in ('loco','hold'):
 key='Skill/'+skill+'_';n=b[key+'episodes']-a[key+'episodes'];steps=b[key+'valid_amp_steps']-a[key+'valid_amp_steps']
 skills[skill]=dict(completed_episodes_approx=n,completed_steps_approx=steps,mean_steps_approx=steps/n,
   success_delta_approx=b[key+'successes']-a[key+'successes'])
total=sum(v['completed_steps_approx'] for v in skills.values())
for val in skills.values():val['completed_step_fraction_approx']=val['completed_steps_approx']/total
keys=['Mean episode length','Control/physical_target_clipped_fraction','Reward/task_weighted_per_step','Reward/amp_per_step','Mean box_position loss','Iteration time']
r=dict(status='PASS',checkpoint=str(ckpt),checkpoint_sha256=hashlib.sha256(ckpt.read_bytes()).hexdigest(),
 source_hashes=prev['archived_sources'],log_snapshot_sha256=hashlib.sha256(raw).hexdigest(),last_iteration=b['iteration'],
 first_recent=rows[-250]['iteration'],recent_means={k:st.mean(row[k] for row in rows[-250:]) for k in keys},
 skill_window=skills,policy_std=x['model_state_dict']['log_std'].exp().tolist(),
 training_pid4038923_exists=Path('/proc/4038923').exists(),limits=['Skill deltas from rollout-averaged/rounded cumulative logs; approximate completed-step share, not exact rollout allocation','Exit reason unknown; no process stopped here'])
(DOC/'training_audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
