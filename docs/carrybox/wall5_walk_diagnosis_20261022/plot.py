"""Plot recorded evidence only; no training or policy changes."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent
fig,axes=plt.subplots(1,3,figsize=(15,4.2))
for name,color in [('rev22','#2075b4'),('rev23','#d34b3e')]:
 rows=json.loads((D/f'{name}_curve.json').read_text());rows=[r for r in rows if r['iteration']<=6900]
 x=np.array([r['iteration'] for r in rows]);v=np.array([r['Mean episode length'] for r in rows])
 axes[0].plot(x[99:],np.convolve(v,np.ones(100)/100,'valid'),color=color,label=name)
axes[0].set(title='Training: mean episode length',xlabel='Iteration',ylabel='Policy steps (100-iteration mean)')
data=json.loads((D/'on.json').read_text())
for name,label,color in [('previous_no_push','rev22 model6400','#2075b4'),('current_no_push','rev23 model6200','#d34b3e')]:
 case=data['cases'][name];trace=case['env0_trace'];trace=[t for t in trace if t['steps']<50]
 x=[t['steps']*.02 for t in trace]
 end=case['episodes'][0]
 roll_x=x+([end['steps']*.02] if end['steps']<50 else [])
 roll_y=[t['roll'] for t in trace]+([end['roll']] if end['steps']<50 else [])
 axes[1].plot(roll_x,roll_y,color=color,label=label)
 j=case['joint_names'].index('left_knee_joint')
 axes[2].plot(x,[t['target'][j] for t in trace],color=color,label=label)
axes[1].axhline(-.5,color='gray',linestyle='--');axes[1].axhline(.5,color='gray',linestyle='--')
axes[1].set(title='Same RSI start, self collision on, no push',xlabel='Time (s)',ylabel='Pelvis roll (rad)')
axes[2].set(title='Raw left knee target before limit clipping, env0',xlabel='Time (s)',ylabel='Joint target (rad)')
for a in axes:a.grid(alpha=.2);a.legend(fontsize=8)
fig.tight_layout();fig.savefig(D/'evidence.png',dpi=150);plt.close(fig)
