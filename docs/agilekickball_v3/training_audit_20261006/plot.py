"""Descriptive learning curves, same training budget but different task distributions."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
out=Path(__file__).resolve().parent
a=np.load(out/'scalars.npz')
fig,axes=plt.subplots(3,2,figsize=(13,11),constrained_layout=True)
colors={'v2':'#2878b5','v3':'#d35244'}
def plot(ax,name,tag,scale=1,label=None):
 v=a[name+'::'+tag]*scale
 n=len(v)//1000
 y=np.nanmean(v[:n*1000].reshape(n,1000),axis=1)
 ax.plot(np.arange(n)*1000+499.5,y,color=colors[name],label=label or name,linewidth=2)
for name in colors:
 p='Agile'+name.upper()+'/'
 plot(axes[0,0],name,p+'course_upper_m_s')
 plot(axes[0,1],name,p+'recent_recovered_serve_share',100)
 plot(axes[1,0],name,'Train/mean_episode_length',.02)
 plot(axes[1,1],name,'Loss/ball/visible/position_cm_rmse')
plot(axes[2,0],'v3','Loss/outcome/ball_velocity_vector_rmse_m_s',label='v3 future ball velocity')
accepted=a['v3::Loss/outcome/encoder_updates']
fallback=a['v3::Loss/outcome/head_only_batches']
ratios=100*accepted/(accepted+fallback)
axes[2,1].plot(np.arange(50)*1000+499.5,ratios.reshape(50,1000).mean(axis=1),
               color=colors['v3'],label='v3 accepted encoder batches',linewidth=2)
labels=[('Incoming speed curriculum ceiling','m/s'),('Recovered-serve share (logged window)','%'),
        ('Mean training episode duration','seconds'),('Current-ball position error, visible samples','cm, mean logged vector RMSE'),
        ('V3 auxiliary: future ball velocity error','m/s, mean logged vector RMSE'),('V3 auxiliary: encoder update acceptance','% of attempted auxiliary batches')]
for ax,(title,unit) in zip(axes.flat,labels):
 ax.set_title(title);ax.set_ylabel(unit);ax.set_xlabel('Training iteration')
 ax.grid(alpha=.2);ax.legend(loc='best');ax.set_xlim(0,50000)
axes[0,0].set_ylim(0,6.4)
axes[0,1].set_ylim(0,100)
axes[1,0].set_ylim(0,62)
axes[2,1].set_ylim(0,105)
fig.suptitle('V2 vs V3: descriptive training diagnostics\n1 seed each; 1,000-iteration block means; different serving distributions',fontsize=15)
fig.savefig(out/'training_comparison.png',dpi=160)
print(out/'training_comparison.png')
