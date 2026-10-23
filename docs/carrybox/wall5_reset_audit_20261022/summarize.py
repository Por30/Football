from pathlib import Path
import json,statistics,hashlib,datetime
import numpy as np
D=Path(__file__).resolve().parent;R=D.parents[2];S=json.loads((D/'selection.json').read_text());p=json.loads((D/'probe.json').read_text());train=json.loads((D/'training_analysis.json').read_text())
assert p['status']=='PASS' and p['weights_unchanged'] and p['contract_matched']
assert hashlib.sha256(Path(S['checkpoint']).read_bytes()).hexdigest()==S['checkpoint_sha256']
for f,h in S['launch']['source_sha256'].items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h,f
proc=Path(f'/proc/{S["launch"]["pid"]}');cmd=[a.decode() for a in (proc/'cmdline').read_bytes().split(b'\0') if a];assert cmd==S['launch']['command']
assert (proc/'stat').read_text().split(') ',1)[1].split()[19]==S['start_ticks']
flags=('tipped','fell_pelvis','fell_head','fell_hip','box_speed')
initial={}
for group in ('default','loco','pickup','hold'):
 rows=[r for r in p['reset_rows'] if r['kind']==group];assert rows
 initial[group]=dict(count=len(rows),invalid_count=sum(any(r[k] for k in flags) for r in rows),
  **{k+'_count':sum(r[k] for r in rows) for k in flags},
  foot_below_1mm=sum(r['foot_clearance']<-.001 for r in rows),foot_below_10mm=sum(r['foot_clearance']<-.01 for r in rows),
  foot_clearance_min_m=min(r['foot_clearance'] for r in rows),foot_clearance_median_m=statistics.median(r['foot_clearance'] for r in rows),
  root_xy_speed_mean_mps=statistics.mean(r['root_xy_speed'] for r in rows),joint_speed_p95_radps=float(np.percentile([r['joint_speed_max'] for r in rows],95)),
  mid360_min_m=min(r['mid360_height'] for r in rows))
cases={}
for name,c in p['cases'].items():
 assert len(c['episodes'])==64 and len(c['initial'])==64
 cases[name]={}
 for group in ('default','loco','pickup','hold'):
  ep=[e for e in c['episodes'] if e['kind']==group];assert ep
  cases[name][group]=dict(count=len(ep),mean_steps=statistics.mean(e['steps'] for e in ep),median_steps=statistics.median(e['steps'] for e in ep),
   min_steps=min(e['steps'] for e in ep),max_steps=max(e['steps'] for e in ep),within_5steps=sum(e['steps']<=5 for e in ep),within_10steps=sum(e['steps']<=10 for e in ep),
   timeouts=sum(e['timeout'] for e in ep),censored=sum(e['censored'] for e in ep),**{k+'_count':sum(e[k] for e in ep) for k in flags},
   roll_tipped=sum(abs(e['roll'])>.5 for e in ep),pitch_tipped=sum(abs(e['pitch'])>1.1 for e in ep))
result=dict(status='PASS',checked_at=datetime.datetime.now().astimezone().isoformat(),training_iteration=train['iteration'],checkpoint=p['checkpoint'],checkpoint_iteration=p['checkpoint_iteration'],reset_initial=initial,cases=cases,source_unchanged=True,formal_process_untouched=True,push_curriculum_scale=p['push_curriculum_scale'],
 limitations=['64 same-seed first episodes per mode; task success rate not evaluated.','Reset-target control is fixed-pose control, not a stabilizing locomotion controller.','Foot clearance is geometric FK before physics; penetration alone does not establish why a policy falls.'])
(D/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=json.loads((D/'curve.json').read_text());fig,axs=plt.subplots(1,2,figsize=(11,3.6))
y=np.array([r['Mean episode length'] for r in rows]);x=[r['iteration'] for r in rows]
axs[0].plot(x[49:],np.convolve(y,np.ones(50)/50,'valid')*.02);axs[0].set(xlabel='Iteration',ylabel='Episode seconds',title='Training: 50-iteration rolling mean');axs[0].grid(alpha=.2)
groups=['default','loco','pickup','hold'];pos=np.arange(4)
for j,(name,label) in enumerate([('mean','Policy mean'),('sample','Policy sampled'),('reset_target','Hold reset pose')]):
 axs[1].bar(pos+(j-1)*.24,[cases[name][g]['mean_steps']*.02 for g in groups],width=.24,label=label)
axs[1].set_xticks(pos,groups);axs[1].set(ylabel='First episode seconds',title='Same starts, 64 envs per mode');axs[1].legend(fontsize=7);axs[1].grid(axis='y',alpha=.2)
fig.tight_layout();fig.savefig(D/'evidence.png',dpi=160);plt.close(fig)
print('RESET_AUDIT_PASS',json.dumps(result,ensure_ascii=False))
