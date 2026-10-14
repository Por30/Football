"""Read-only analysis of the stopped formal wall4 run, with reproducible curves."""
from pathlib import Path
import csv,json,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parents[1]
out=root/'docs/carrybox/convergence_20261014';out.mkdir(parents=True,exist_ok=True)
log=root/'logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/train.log'
chunks=re.split(r'Learning iteration\s+(\d+)/40000',log.read_text(errors='replace'))
rows=[]
for k in range(1,len(chunks),2):
 row={'iteration':int(chunks[k])}
 for line in chunks[k+1].splitlines():
  match=re.match(r'\s*([^:]+):\s*(-?\d+(?:\.\d+)?)\s*$',line)
  if match:row[match[1].strip()]=float(match[2])
 if 'Mean episode length' in row:rows.append(row)
assert len(rows)>1000
keys=['Mean episode length','Mean reward','Mean amp_valid_samples loss','AMP/valid_fraction','AMP/style_reward','Metrics/episode_lift_success','Episode_Reward/fall','Mean box_position loss']
with (out/'training_curve.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['iteration']+keys);w.writeheader()
 for row in rows:w.writerow({k:row.get(k,0) for k in ['iteration']+keys})
windows={}
for lo,hi in [(0,50),(50,100),(100,200),(200,500),(500,1000),(rows[-1]['iteration']-999,rows[-1]['iteration']+1)]:
 selected=[r for r in rows if lo<=r['iteration']<hi]
 windows[f'{lo}-{hi-1}']={k:float(np.mean([r.get(k,0) for r in selected])) for k in keys}
report=dict(status='PASS',last_iteration=rows[-1]['iteration'],rows=len(rows),windows=windows,
 max_logged_success=max(r.get('Metrics/episode_lift_success',0) for r in rows),
 amp_zero_update_fraction=float(np.mean([r.get('Mean amp_valid_samples loss',0)==0 for r in rows[-1000:]])),
 policy_dt=.02,amp_first_valid_step=9,stopped=True)
(out/'training_analysis.json').write_text(json.dumps(report,indent=2)+'\n')
x=np.array([r['iteration'] for r in rows])
fig,ax=plt.subplots(3,1,figsize=(10,8),sharex=True)
ax[0].plot(x,[r['Mean episode length']*.02 for r in rows],lw=.8)
ax[0].axhline(.18,color='red',ls='--',label='AMP needs 9 post-reset steps');ax[0].legend();ax[0].set_ylabel('Episode length (s)')
ax[1].plot(x,[r.get('Mean amp_valid_samples loss',0)/3072 for r in rows],lw=.8);ax[1].set_ylabel('Valid AMP samples / rollout')
ax[2].plot(x,[r['Mean reward'] for r in rows],lw=.8);ax[2].set_ylabel('Mean episode return');ax[2].set_xlabel('Training iteration')
for a in ax:a.grid(alpha=.2)
fig.suptitle('Stopped G1 Wall4: shorter episodes suppress AMP; return increase is not task progress')
fig.tight_layout();fig.savefig(out/'training_curve.png',dpi=160);plt.close(fig)
print(json.dumps(report,indent=2))
