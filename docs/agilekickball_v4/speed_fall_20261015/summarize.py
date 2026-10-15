"""Summarize already-recorded traces; no simulator execution."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

HERE=Path(__file__).resolve().parent
result=json.loads((HERE/'results.json').read_text())
names=json.loads((HERE.parents[2]/'logs/rsl_rl/agilekickball_v4/2026-10-12_13-48-41_return_to_sender_20261012_v3init/exported/manifest.json').read_text())['metadata']['joint_names']
index=names.index('right_hip_roll_joint')
summary=[]
for r in result['baseline']+result['contrasts']:
    data=np.load(HERE/r['trace_file'])
    trace=data['trace'];time=trace[:,0]
    contact=r['first_contact']
    pre=(time>=contact['time_s']-.2-1e-7)&(time<=contact['time_s']-.02+1e-7) if contact else time<.4
    row={'mode':r['mode'],'speed_m_s':r['speed_m_s'],
         'first_contact_s':contact['time_s'] if contact else None,
         'first_fall_s':r['first_fall']['time_s'] if r['first_fall'] else None,
         'precontact_window_s':[float(time[pre][0]),float(time[pre][-1])],
         'precontact_right_hip_roll_requested_peak_Nm':float(data['max_requested_torque'][pre,index].max()),
         'precontact_right_hip_roll_saturation_fraction':float(data['saturation'][pre,index].mean())}
    if r['speed_m_s']==4 and r['mode']=='policy':
        row['samples']=[{'time_s':float(trace[j,0]),'tilt_deg':float(trace[j,2]),
                        'com_vx_m_s':float(trace[j,18]),
                        'com_loaded_foot_aabb_margin_m':float(trace[j,21]) if np.isfinite(trace[j,21]) else None,
                        'loaded_feet':data['feet_support'][j].tolist()}
                       for t in (.4,.5,.6,1.,1.38) for j in [int(np.argmin(abs(time-t)))]]
    summary.append(row)
(HERE/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,axes=plt.subplots(3,1,figsize=(10,9),sharex=True,layout='constrained')
labels={'policy':'4 m/s, current model','ghost':'4 m/s, no ball-robot contact',
        'training_hip_roll_limit':'4 m/s, diagnostic hip-roll limit 139 Nm'}
for r in result['baseline']+result['contrasts']:
    if r['speed_m_s']!=4 or r['mode'] not in labels:continue
    data=np.load(HERE/r['trace_file']);trace=data['trace']
    for ax,col in [(axes[0],2),(axes[2],21)]:
        ax.plot(trace[:,0],trace[:,col],label=labels[r['mode']])
    if r['mode']=='policy':
        axes[1].plot(trace[:,0],data['max_requested_torque'][:,index],color='#b94e39',label='Requested |right hip-roll torque|')
for ax in axes:
    ax.axvline(.42,color='#777',linestyle=':',label='First ball contact in current model' if ax is axes[0] else None)
    ax.grid(alpha=.2)
axes[0].axhline(35,color='#999',linestyle='--')
axes[0].set_ylabel('Pelvis tilt [deg]');axes[0].legend(fontsize=8)
axes[1].axhline(88,color='#333',linestyle='--',label='Current limit: 88 Nm')
axes[1].axhline(139,color='#666',linestyle=':',label='Training limit: 139 Nm')
axes[1].set_ylabel('Requested torque [Nm]');axes[1].legend(fontsize=8)
axes[2].axhline(0,color='#999',linestyle='--');axes[2].set_ylabel('COM to loaded-foot\nXY bounding box [m]')
axes[2].set_xlabel('Simulation time [s]');axes[2].set_xlim(0,3)
axes[0].set_title('Fast-ball failure: contact, actuator capacity and recovery\nSingle deterministic diagnostic; no success-rate claim')
fig.savefig(HERE/'diagnosis.png',dpi=150)
plt.close(fig)
print(json.dumps(summary,indent=2))
