"""Descriptive paired-pilot curves, never labelled as independent task success."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent
fig,axes=plt.subplots(2,2,figsize=(10,6),layout='constrained')
for name,path in [('balance weight 2',P/'attempt1/pilot.json'),('balance weight 5',P/'pilot.json')]:
 d=json.loads(path.read_text());rows=d['rows'];xs=[];length=[];reward=[];sat=[];std=[]
 for end in range(25,201,25):
  group=rows[end-25:end];last=group[-1];before=rows[end-26] if end>25 else {'episode_counts':[0]*3,'episode_steps':[0]*3}
  count=last['episode_counts'][0]-before['episode_counts'][0]
  xs.append(end);length.append((last['episode_steps'][0]-before['episode_steps'][0])/max(1,count))
  reward.append(sum(r['metrics']['Reward/loco_task_per_step']-r['metrics']['Reward/loco_early_failure_per_step'] for r in group)/25)
  sat.append(sum(r['metrics']['Control/physical_target_clipped_fraction'] for r in group)/25*100)
  std.append(sum(r['loss']['action_std_max'] for r in group)/25)
 for ax,y in zip(axes.flat,[length,reward,sat,std]):ax.plot(xs,y,'o-',label=name)
for ax,title,ylabel in zip(axes.flat,['Completed loco episode length','Loco task excluding failure event','Physical target clipping, all skills','Largest policy action std'],['policy steps','raw task reward / policy step','percent','raw action std']):
 ax.set(title=title,xlabel='training iteration (25-iteration windows)',ylabel=ylabel);ax.grid(alpha=.25)
axes[0,0].legend();axes[0,1].axhline(0,color='gray',lw=.8);axes[1,1].axhline(1,color='gray',lw=.8)
fig.suptitle('Wall5 fresh pilots: 512 environments, seed 42, 200 iterations\nEngineering diagnostic; not an independent walking or lifting evaluation',fontsize=11)
fig.savefig(P/'pilot_comparison.png',dpi=150);plt.close(fig)
