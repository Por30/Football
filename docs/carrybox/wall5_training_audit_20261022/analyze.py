from pathlib import Path
import json,re,statistics,hashlib
D=Path(__file__).resolve().parent;S=json.loads((D/'selection.json').read_text())
raw=Path(S['launch']['log']).read_bytes();(D/'training_snapshot.log').write_bytes(raw)
chunks=re.split(r'Learning iteration\s+(\d+)/40000',raw.decode(errors='replace'));rows=[]
for i in range(1,len(chunks),2):
 r={'iteration':int(chunks[i])}
 for line in chunks[i+1].splitlines():
  m=re.match(r'\s*([^:\x1b]+):\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)s?\s*$',line)
  if m:r[m[1].strip()]=float(m[2])
 if 'Mean episode length' in r and 'Iteration time' in r:rows.append(r)
assert len(rows)>100
(D/'curve.json').write_text(json.dumps(rows)+'\n')
keys=['Mean episode length','Mean reward','Iteration time','Reset/default_fraction','Reset/loco_rsi_fraction','Reset/pickup_rsi_fraction','Reset/hold_rsi_fraction','Sampling/loco_transition_fraction','Sampling/pickup_transition_fraction','Sampling/hold_transition_fraction','Reward/loco_task_per_step','Reward/loco_walk_task_per_step','Reward/loco_torques_per_step','Reward/loco_action_rate_per_step','AMP/style_reward','Mean box_aux_weighted loss','Reward/mixed_per_step','Mean amp_expert_loss loss','Mean amp_policy_loss loss','Mean ppo_learning_rate loss','Mean box_visible_fraction loss']
windows={}
for lo,hi in [(0,100),(100,300),(300,600),(600,900),(rows[-1]['iteration']-99,rows[-1]['iteration']+1)]:
 subset=[r for r in rows if lo<=r['iteration']<hi]
 if subset:windows[f'{lo}:{hi}']={k:statistics.mean(r[k] for r in subset) for k in keys}
a=rows[-101];b=rows[-1];recent={}
for skill in ('loco','pickup','hold'):
 key=f'Skill/{skill}_';n=b[key+'episodes']-a[key+'episodes'];steps=b[key+'valid_amp_steps']-a[key+'valid_amp_steps']
 recent[skill]={'estimated_completed_episodes':n,'mean_steps_from_cumulative_difference':steps/n,'seconds':.02*steps/n}
 for flag in ('tilt_at_episode_end','fell','fell_pelvis','fell_head','fell_hip'):
  recent[skill][flag+'_fraction_from_rounded_counters']=(b[key+flag+'_fraction']*b[key+'episodes']-a[key+flag+'_fraction']*a[key+'episodes'])/n
result=dict(status='PASS',iteration=rows[-1]['iteration'],logged_rows=len(rows),last=rows[-1],windows=windows,recent_completed_estimates=recent,policy_dt=.02,
 source_log_sha256=hashlib.sha256(raw).hexdigest(),limitations=['Skill counters are averaged over a logging interval; differences are estimates. Loco includes default starts.','Episode_Termination tags are latest per-env cause occupancy, not recent completed-episode fractions.'])
(D/'training_analysis.json').write_text(json.dumps(result,indent=2)+'\n');print('LOG_ANALYSIS_PASS',result['iteration'],json.dumps(recent))
