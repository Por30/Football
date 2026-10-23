"""Readable physical-target diagnostics, always exclude startup and reset."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent
S=json.loads((D/'selection.json').read_text());O=Path(S['video']).parent
m=json.loads((D/'baseline_trace.json').read_text());n=m['joint_names'];a=np.load(D/'baseline_trace.npz')
assert not a['reset'][:999].any() and a['reset'][999].all()
result=[]
for env in range(4):
 knees=[];ankles=[]
 for side in ('left','right'):
  j=n.index(side+'_knee_joint');sat=a['saturation'][400:,env,j];p=a['processed'][400:,env,j]
  assert np.allclose(p[sat],-.087267,atol=1e-5)
  knees.append(dict(side=side,clipped_fraction=float(sat.mean()),clamped_target_deg=-5.,
    measured_q_median_deg=float(np.median(a['q'][400:,env,j])*180/np.pi)))
  j=n.index(side+'_ankle_pitch_joint');p=a['processed'][400::4,env,j]
  x=a['qd'][400:,env,j].astype(float);f=np.fft.rfftfreq(len(x),.005)
  v=np.abs(np.fft.rfft((x-x.mean())*np.hanning(len(x))))**2;mask=(f>=2)&(f<25)
  ankles.append(dict(side=side,target_20ms_change_rms_deg=float(np.sqrt(np.mean(np.diff(p)**2))*180/np.pi),
    velocity_peak_in_2_25hz=float(f[mask][np.argmax(v[mask])]),q_std_deg=float(np.std(a['q'][400:,env,j])*180/np.pi)))
 result.append(dict(robot=env+1,window_s=[2,20],knees=knees,ankles=ankles))
(D/'target_details.json').write_text(json.dumps(result,indent=2)+'\n')
fig,axs=plt.subplots(3,1,figsize=(12,9),constrained_layout=True)
t=np.arange(4000)*.005;i=1;j=n.index('left_knee_joint')
axs[0].plot(t[400:1600],a['processed'][400:1600,i,j]*180/np.pi,label='Clamped target')
axs[0].plot(t[400:1600],a['q'][400:1600,i,j]*180/np.pi,label='Actual knee')
axs[0].set(title='Robot2: knee target fixed at lower limit; changing ankle targets',ylabel='Knee angle (deg)')
j=n.index('right_ankle_pitch_joint')
axs[1].plot(t[400:1600],a['target'][400:1600,i,j]*180/np.pi,label='Actual delayed target')
axs[1].plot(t[400:1600],a['q'][400:1600,i,j]*180/np.pi,label='Actual ankle')
axs[1].set(ylabel='Ankle angle (deg)',xlabel='Time (s)')
for side,offset in [('left',-.18),('right',.18)]:
 vals=[100*next(x for x in row['knees'] if x['side']==side)['clipped_fraction'] for row in result]
 axs[2].bar(np.arange(4)+offset,vals,.36,label=side+' knee')
axs[2].set(xticks=np.arange(4),xticklabels=['Default','Loco1','Loco2','Hold'],ylabel='Clipped physical steps (%)',ylim=(0,110))
for ax in axs:ax.legend();ax.grid(alpha=.3)
fig.savefig(O/'target_saturation.png',dpi=140);plt.close(fig)
print('TARGET_DETAILS_OK',json.dumps(result))
