"""Read-only numerical diagnosis of an existing training run."""
from pathlib import Path
import json,re,statistics,datetime,torch
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
RUN=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_21-08-12_wall4_handoff_v6_amp15_20261014_210808'
log=Path('/proc/2448113/fd/1'); text=log.read_text(); rows=[]
for block in re.split(r'Learning iteration ',text)[1:]:
 m=re.match(r'(\d+)/',block)
 if not m or 'Iteration time:' not in block:continue
 row={'iteration':int(m[1])}
 for line in block.splitlines():
  m=re.match(r'\s*([^:]+):\s*(-?\d+(?:\.\d+)?)(?:s)?\s*$',line)
  if m:row[m[1].strip()]=float(m[2])
 rows.append(row)
keys=['Mean reward','Mean episode length','Mean action noise std','AMP/style_reward','AMP/valid_fraction','Episode_Termination/tipped','Episode_Termination/time_out','Metrics/episode_lift_success','Episode_Reward/walk_task','Episode_Reward/carryup_task','Episode_Reward/standup_task','Episode_Reward/grip_force_cap','Mean amp_expert_loss loss','Mean amp_policy_loss loss','Iteration time']
windows={}
for low,high in [(0,99),(900,999),(3500,3599),(6900,6999),(9900,9999),(rows[-1]['iteration']-99,rows[-1]['iteration'])]:
 selected=[r for r in rows if low<=r['iteration']<=high]
 windows[f'{low}-{high}']={k:statistics.mean([r[k] for r in selected if k in r]) for k in keys if any(k in r for r in selected)}
checkpoints={}
for i in [0,3600,13600]:
 c=torch.load(RUN/f'model_{i}.pt',map_location='cpu',weights_only=False)
 checkpoints[str(i)]={'schema':c['carrybox_schema'],'env':c['environment_contract'],'amp_config':c['amp']['config'],'dataset':c['amp']['dataset'],'noise_std':c['model_state_dict']['log_std'].exp().tolist(),'finite':all(torch.isfinite(v).all().item() for v in c['model_state_dict'].values())}
 assert checkpoints[str(i)]['finite']
report={'checked_at':datetime.datetime.now().isoformat(),'log_actual_path':str(log.resolve()),'last_complete_iteration':rows[-1]['iteration'],'iteration_windows':windows,'checkpoints':checkpoints,'success_max':max(r.get('Metrics/episode_lift_success',0) for r in rows),'success_nonzero_iterations':sum(r.get('Metrics/episode_lift_success',0)>0 for r in rows),'sampled_iterations':len(rows)}
(OUT/'training_summary.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'training_rows.json').write_text(json.dumps(rows)+'\n')
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(2,2,figsize=(11,7))
for ax,key in zip(axes.flat,['Mean episode length','Metrics/episode_lift_success','Episode_Termination/tipped','AMP/style_reward']):
 chunks=[rows[j:j+100] for j in range(0,len(rows),100)]
 ax.plot([statistics.mean(r['iteration'] for r in c) for c in chunks],[statistics.mean(r.get(key,0) for r in c) for c in chunks]);ax.set_title(key);ax.set_xlabel('iteration');ax.grid(alpha=.25)
fig.tight_layout();fig.savefig(OUT/'training_curves.png',dpi=140)
print(json.dumps({k:v for k,v in report.items() if k!='checkpoints'},indent=2))
