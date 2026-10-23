from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent
conditions=[('Quota only',D/'quota_only/validate.log'),('Quota + alive 1',D/'alive_weight1/validate.log'),('Quota + alive 3',D/'validate.log')]
fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
for label,path in conditions:
 rows=[json.loads(line[6:]) for line in path.read_text().splitlines() if line.startswith('PILOT ')]
 for ax,key in zip(axes,('default','loco')):
  ax.plot([r['iteration'] for r in rows],[r['recent_completed_steps'][key] for r in rows],marker='o',ms=3,label=label)
for ax,title in zip(axes,('Default empty-hand starts','Locomotion RSI starts')):
 ax.set(title=title,xlabel='PPO / AMP update');ax.grid(alpha=.25);ax.legend(fontsize=9)
axes[0].set_ylabel('Recent completed episode length (steps, 50 Hz)')
fig.suptitle('512 environments, seed 42, fresh initialization; last 200 completed episodes per source')
fig.tight_layout();fig.savefig(D/'pilot_comparison.png',dpi=150);plt.close(fig)
