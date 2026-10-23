"""Compare the same telemetry and initial states, under the same curriculum."""
from pathlib import Path
import hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent;S=json.loads((D/'selection.json').read_text());P=Path(S['previous_directory']);O=Path(S['video']).parent
assert hashlib.sha256((P/'baseline_trace.npz').read_bytes()).hexdigest()==S['previous_trace_sha256']
r=json.loads((D/'recording.json').read_text());previous=json.loads((P/'recording.json').read_text())
assert r['environment_contract']==previous['environment_contract']
assert r['playback_curriculum_iteration']==2200 and r['yaw_degrees']==previous['yaw_degrees'] and r['push_scale']==previous['push_scale']
assert max(json.loads((D/'initial_match.json').read_text()).values())<=2e-5
names=json.loads((D/'baseline_trace.json').read_text())['joint_names']
assert names==json.loads((P/'baseline_trace.json').read_text())['joint_names']
leg=[i for i,n in enumerate(names) if any(k in n for k in ('hip','knee','ankle'))]
knees=[names.index(n) for n in ('left_knee_joint','right_knee_joint')]
a={'previous':np.load(P/'baseline_trace.npz'),'latest':np.load(D/'baseline_trace.npz')}
for data in a.values():
 assert data['q'].shape==(4000,4,29) and data['action'].shape==(1000,4,29)
 assert all(np.isfinite(data[k]).all() for k in data.files)
 assert np.all(np.diff(data['physical_step'])==1)
ends={label:[int(np.flatnonzero(data['reset'][:,i])[0])+1 if data['reset'][:,i].any() else 1000 for i in range(4)] for label,data in a.items()}
stop=min(x for v in ends.values() for x in v);start=400;end=4*stop
sufficient=end-start>=200
result={}
for label,data in a.items():
 rows=[]
 for i in range(4):
  row=dict(robot=i+1,first_episode_steps=ends[label][i])
  if sufficient:
   qd=data['qd'][start:end,i][:,leg].astype(float);freq=np.fft.rfftfreq(len(qd),.005)
   spectrum=np.abs(np.fft.rfft((qd-qd.mean(0))*np.hanning(len(qd))[:,None],axis=0))**2
   root=data['root'][start:end,i]
   row.update(joint_velocity_rms_rad_s=float(np.sqrt(np.mean(qd**2))),
    joint_acceleration_rms_rad_s2=float(np.sqrt(np.mean((np.diff(qd,axis=0)/.005)**2))),
    action_step_rms=float(np.sqrt(np.mean(np.diff(data['action'][start//4:stop,i][:,leg],axis=0)**2))),
    knee_target_clipped_fraction=data['saturation'][start:end,i][:,knees].mean(0).tolist(),
    velocity_power_fraction_ge8hz=float(spectrum[freq>=8].sum()/spectrum[1:].sum()),
    self_contact_fraction_gt1n=float((data['self_contact_max'][start:end,i]>1).mean()),
    root_xy_speed_mean_mps=float(np.linalg.norm(root[:,7:9],axis=-1).mean()),
    root_xy_net_displacement_m=float(np.linalg.norm(root[-1,:2]-root[0,:2])))
  rows.append(row)
 result[label]=rows
behavior=[];traj=json.loads((D/'trajectory.json').read_text())
for i in range(4):
 rows=[x for x in traj[:ends['latest'][i]-1] if not x['reset'][i]]
 if rows:
  robot=np.array([x['robot'][i] for x in rows]);box=np.array([x['box'][i] for x in rows]);d=np.linalg.norm((robot-box)[:,:2],axis=1)
  behavior.append(dict(robot=i+1,distance_xy_start_m=float(d[0]),distance_xy_end_m=float(d[-1]),distance_xy_min_m=float(d.min()),root_xy_net_displacement_m=float(np.linalg.norm(robot[-1,:2]-robot[0,:2])),any_hand_contact_steps=sum(any(x['hand_contacts'][i]) for x in rows),bilateral_contact_steps=sum(all(x['hand_contacts'][i]) for x in rows),initial_box_bottom_m=rows[0]['box_bottom_clearance'][i],final_box_bottom_m=rows[-1]['box_bottom_clearance'][i]))
output=dict(status='PASS',previous_model=2800,latest_model=S['checkpoint_iteration'],same_initial_state=True,
 curriculum_iteration=2200,push_scale=r['push_scale'],yaw_degrees=r['yaw_degrees'],joint_names=names,
 paired_global_stop_step=stop,analysis_window_seconds=[2.,stop*.02] if sufficient else None,
 enough_common_samples=sufficient,metrics=result,latest_behavior=behavior,
 limitations=['One seed, four starts; no general convergence or success-rate claim.','Curriculum fixed at2200 for comparison, not current formal training iteration.','Acceleration RMS includes contact impacts and changed movement; not a pure jitter score.','Knee saturation is command clipping, not a measurement of joint-limit contact.','Metrics exclude startup2s and stop before any reset changes the shared random stream.'])
if sufficient:
 output['acceleration_change_percent']=[100*(new['joint_acceleration_rms_rad_s2']/old['joint_acceleration_rms_rad_s2']-1) for old,new in zip(result['previous'],result['latest'])]
 fig,axs=plt.subplots(2,1,figsize=(10,7),constrained_layout=True)
 x=np.arange(4)
 for label,offset,model in [('previous',-.18,2800),('latest',.18,S['checkpoint_iteration'])]:
  axs[0].bar(x+offset,[v['joint_acceleration_rms_rad_s2'] for v in result[label]],.36,label=f'model{model}')
  axs[1].bar(x+offset,[100*np.mean(v['knee_target_clipped_fraction']) for v in result[label]],.36,label=f'model{model}')
 axs[0].set(ylabel='Leg acceleration RMS (rad/s²)',title='Matched starts and curriculum; first-episode comparison')
 axs[1].set(ylabel='Knee targets clipped (%)',ylim=(0,105))
 for ax in axs:ax.set_xticks(x,['Default','Loco1','Loco2','Hold']);ax.grid(axis='y',alpha=.3);ax.legend()
 fig.savefig(O/'comparison.png',dpi=140);plt.close(fig)
(D/'comparison.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output,indent=2));print('COMPARISON_PASS')
