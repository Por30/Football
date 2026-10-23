"""Paired first-episode kinematics; no FFT or differences across resets."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent;R=D.parents[2]
S=json.loads((D/'selection.json').read_text());O=Path(S['video']).parent
modes=('baseline','no_self','no_delay')
a={k:np.load(D/f'{k}_trace.npz') for k in modes}
meta={k:json.loads((D/f'{k}_trace.json').read_text()) for k in modes}
joints=meta['baseline']['joint_names']
legs=[i for i,n in enumerate(joints) if any(x in n for x in ('hip','knee','ankle'))]
results={k:[] for k in modes}
first=np.array([[int(np.flatnonzero(a[k]['reset'][:,i])[0])+1 if a[k]['reset'][:,i].any() else 1000 for i in range(4)] for k in modes])
# An early reset anywhere can alter the shared RNG stream; cap all paired windows there.
common_end=int(first.min());start=400;end=4*common_end
assert end-start>=200, (start,end)
assert all(a[k]['q'].shape==(4000,4,29) for k in modes)
assert all(np.isfinite(a[k][n]).all() for k in modes for n in a[k].files)
assert a['no_self']['self_contact_max'].max()<1e-4
assert np.all(a['no_delay']['delay_index']==4)
for k in modes:
 assert np.all(np.diff(a[k]['physical_step'])==1)
 assert np.max(np.abs(np.diff(a[k]['timestamp'])-.005))<1e-5
 for i in range(4):
  qd=a[k]['qd'][start:end,i][:,legs].astype(float);n=len(qd);window=np.hanning(n)[:,None]
  spec=np.abs(np.fft.rfft((qd-qd.mean(0))*window,axis=0))**2
  freq=np.fft.rfftfreq(n,.005);total=spec[1:].sum();band=spec[freq>=8].sum()
  action=a[k]['action'][start//4:common_end,i][:,legs]
  target=a[k]['target'][start:end,i][:,legs]
  max_per_joint=spec[(freq>=1)&(freq<=80)].sum(0);j=int(np.argmax(max_per_joint))
  fmask=(freq>=1)&(freq<=80);dom=float(freq[fmask][np.argmax(spec[fmask,j])])
  root=a[k]['root'][start:end,i]
  contacts=a[k]['self_contact_max'][start:end,i]
  result=dict(env_id=i,initial_kind=['default','loco','loco','hold'][i],first_episode_steps=int(first[modes.index(k),i]),
    paired_window_seconds=[start*.005,end*.005],joint_velocity_rms_rad_s=float(np.sqrt(np.mean(qd**2))),
    joint_acceleration_rms_rad_s2=float(np.sqrt(np.mean((np.diff(qd,axis=0)/.005)**2))),
    action_step_rms=float(np.sqrt(np.mean(np.diff(action,axis=0)**2))),
    actual_target_step_rms_rad=float(np.sqrt(np.mean(np.diff(target,axis=0)**2))),
    joint_velocity_power_fraction_ge8hz=float(band/total) if total else 0.,
    highest_velocity_power_joint=joints[legs[j]],dominant_frequency_hz=dom,
    self_contact_peak_n=float(contacts.max()),self_contact_fraction_gt1n=float(np.mean(contacts>1)),
    estimated_pd_torque_rms_nm=float(np.sqrt(np.mean(a[k]['torque'][start:end,i][:,legs]**2))),
    root_xy_net_displacement_m=float(np.linalg.norm(root[-1,:2]-root[0,:2])),
    root_xy_speed_mean_mps=float(np.linalg.norm(root[:,7:9],axis=-1).mean()),
    saturation_fraction=float(a[k]['saturation'][start:end,i][:,legs].mean()))
  results[k].append(result)
# Preserve deduplicated body-pair peaks; pair net force does not measure every contact point.
pairs={}
for k in modes:
 d={}
 for x in meta[k]['internal_contact_pairs']:
  key=(x['env_id'],*sorted((x['a'],x['b'])))
  d[key]=max(d.get(key,0.),x['peak_n'])
 pairs[k]=[dict(env_id=i,a=x,b=y,peak_n=f) for (i,x,y),f in sorted(d.items(),key=lambda x:-x[1])]
result=dict(status='PASS',checkpoint=S['checkpoint'],conditions=results,internal_contact_pairs=pairs,
 paired_global_stop_control_step=common_end,fft_window_seconds=(end-start)*.005,frequency_resolution_hz=200/(end-start),
 limitations=['4env single-seed diagnostic, not overall success-rate evidence.','All comparisons use common first-episode prefix, exclude first2s startup and never cross reset.','Closed-loop trajectories may diverge under overrides; smaller RMS alone does not prove a sole cause.','25fps video can alias motion above12.5Hz; motion spectra use200Hz physical telemetry.','Implicit actuator applied_torque is a PD estimate, not solver-measured motor torque.','Pair forces are vector sums and do not enumerate individual contact points.'])
(D/'jitter_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
fig,axes=plt.subplots(3,1,figsize=(12,10),constrained_layout=True)
i=0;j=next(i for i,n in enumerate(joints) if n=='left_knee_joint');t=np.arange(4000)*.005
for k in modes:
 axes[0].plot(t[400:800],a[k]['q'][400:800,i,j],label=k)
 axes[1].plot(t[400:800],a[k]['target'][400:800,i,j],label=k)
 qd=a[k]['qd'][start:end,i,j].astype(float);f=np.fft.rfftfreq(len(qd),.005)
 power=np.abs(np.fft.rfft((qd-qd.mean())*np.hanning(len(qd))))**2
 axes[2].semilogy(f[1:],np.maximum(power[1:],1e-10),label=k)
axes[0].set(ylabel='Knee position (rad)',title=f'Model {S["checkpoint_iteration"]}, Robot1 default, left knee')
axes[1].set(ylabel='Actual delayed target (rad)',xlabel='Time (s)')
axes[2].set(xlabel='Frequency (Hz)',ylabel='Velocity spectral power',xlim=(0,50))
for ax in axes:ax.legend();ax.grid(alpha=.3)
fig.savefig(O/'jitter_comparison.png',dpi=140);plt.close(fig)
print(json.dumps(result,indent=2));print('JITTER_CHECK_PASS')
