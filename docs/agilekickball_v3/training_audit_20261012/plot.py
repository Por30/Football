from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
out=Path(__file__).resolve().parent
prior=np.load(out.parent/'stability_fix_20261008/scalars.npz')
current=np.load(out/'scalars.npz')
fig,axes=plt.subplots(1,3,figsize=(12,3.5),constrained_layout=True)
for version,source,prefix,course,label,color in [
 ('v2',prior,'v2::','AgileV2/','V2 baseline','#247aab'),
 ('failed',prior,'v3::','AgileV3/','Failed V3 (Oct 6)','#cc6045'),
 ('current',current,'','AgileV3/','Current V3 (V2 initialized)','#238865')]:
 for ax,tag,factor,ylabel in zip(axes,['Train/mean_episode_length',course+'recent_recovered_serve_share',course+'course_upper_m_s'],[.02,100,1],['Episode length (s)','Recent recovered-serve share (%)','Curriculum speed ceiling (m/s)']):
  y=source[prefix+tag]*factor
  ax.plot(np.arange(len(y)).reshape(-1,500).mean(1),y.reshape(-1,500).mean(1),label=label,color=color,linewidth=1.8)
  ax.set_xlabel('Training iteration');ax.set_ylabel(ylabel);ax.grid(alpha=.2)
axes[0].legend(frameon=False,fontsize=8)
fig.suptitle('Training diagnostics: single runs with different initialization and adaptive sampling',fontsize=10)
fig.savefig(out/'training_comparison.png',dpi=180)
