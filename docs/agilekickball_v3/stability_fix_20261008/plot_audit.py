from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
out=Path(__file__).resolve().parent
arrays=np.load(out/'scalars.npz')
fig,axes=plt.subplots(1,3,figsize=(12,3.4),constrained_layout=True)
for name,color,label in [('v2','#147d92','V2 baseline'),('v3','#d65f3e','Failed V3, Oct 6')]:
 for ax,tag,factor,ylabel in zip(axes,['Train/mean_episode_length',f'Agile{name.upper()}/recent_recovered_serve_share',f'Agile{name.upper()}/course_upper_m_s'],[.02,100,1],['Episode length (s)','Recent recovered-serve share (%)','Curriculum speed ceiling (m/s)']):
  values=arrays[name+'::'+tag]*factor
  x=np.arange(len(values)).reshape(-1,500).mean(1)
  y=values.reshape(-1,500).mean(1)
  ax.plot(x,y,color=color,label=label,linewidth=1.8)
  ax.set_xlabel('Training iteration');ax.set_ylabel(ylabel);ax.grid(alpha=.18)
axes[0].legend(frameon=False)
fig.suptitle('Completed runs: training diagnostics, one seed each; adaptive sampling distributions differ',fontsize=10)
fig.savefig(out/'training_audit.png',dpi=180)
fig.savefig(out/'training_audit.svg')
