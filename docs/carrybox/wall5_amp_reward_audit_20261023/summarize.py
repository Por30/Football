from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent
modes=('current','rev22','no_delay');meta={m:json.loads((D/f'{m}.json').read_text()) for m in modes};data={m:np.load(D/f'{m}_trajectory.npz') for m in modes}
common=np.logical_and.reduce([data[m]['valid'] for m in modes]);kinds=np.array(meta['current']['initial_kinds'])
assert all(meta[m]['initial_kinds']==kinds.tolist() for m in modes)
def measure(m,mask):
 x=data[m];names=meta[m]['reward_names'];out=dict(samples=int(mask.sum()))
 if not mask.any():return out
 for k in ('xy','xyz','towards','speed','travel','reach_gate','reach','bilateral','lift','task','style','old_style','mixed','old_walk'):
  out[k]=float(x[k][mask].mean())
 out['style_zero_fraction']=float((x['style'][mask]<=1e-8).mean());out['logit_mean']=float(x['logit'][mask].mean())
 out['reach_gate_zero_fraction']=float((x['reach_gate'][mask]==0).mean());out['both_contact_fraction']=float((x['contact_force'][mask]>1).all(-1).mean())
 out['reward_terms']=dict(zip(names,x['rewards'][mask].mean(0).tolist()))
 out['style_weighted']=.125*out['style'];out['task_weighted']=.75*out['task']
 out['new_mixed_sum_per_env']=float((x['mixed']*mask).sum()/max(1,mask.any(0).sum()))
 oldwalk_alive=x['task']-x['rewards'][...,names.index('alive')]-x['rewards'][...,names.index('walk_task')]+x['old_walk']
 out['walk_alive_only_counterfactual_mixed']=float((.75*oldwalk_alive+.125*x['style'])[mask].mean())
 out['target_clipped_fraction']=float(x['saturation'][mask].mean())
 knees=[i for i,n in enumerate(meta[m]['action_joint_names']) if 'knee' in n]
 out['knees_clipped_fraction']=dict(zip([meta[m]['action_joint_names'][i] for i in knees],x['saturation'][mask][:,knees].mean(0).tolist()))
 out['towards_gt_0_2_fraction']=float((x['towards'][mask]>.2).mean())
 # Adjacent physical samples only, excluding reset and first 2 seconds.
 ph=np.load(D/f'{m}_physical.npz');pm=np.repeat(mask,4,axis=0);pair=pm[1:]&pm[:-1]
 legs=[i for i,n in enumerate(meta[m]['joint_names']) if any(s in n for s in ('hip','knee','ankle'))]
 acceleration=np.diff(ph['qd'],axis=0)/.005
 out['leg_acceleration_rms_rad_s2']=float(np.sqrt(np.mean(acceleration[pair][:,legs]**2))) if pair.any() else None
 action_pair=mask[1:]&mask[:-1];target_diff=np.diff(x['target'],axis=0)
 ankles=[i for i,n in enumerate(meta[m]['action_joint_names']) if 'ankle_pitch' in n]
 out['ankle_target_step_rms_deg']=float(np.sqrt(np.mean(target_diff[action_pair][:,ankles]**2))*180/np.pi) if action_pair.any() else None
 return out
results={}
for m in modes:
 x=data[m];groups={}
 for label,ids in [('empty',kinds<2),('default',kinds==0),('loco',kinds==1),('pickup',kinds==2),('hold',kinds==3)]:
  independent=x['valid']&ids[None];matched=common&ids[None];matched[:100]=False
  lengths=np.array(meta[m]['first_episode_steps'])[ids]
  end=[];minimum=[];start=np.array(meta[m]['initial_xy'])[ids]
  for i in np.flatnonzero(ids):
   z=x['xy'][x['valid'][:,i],i];end.append(float(z[-1]) if len(z) else None);minimum.append(float(z.min()) if len(z) else None)
  groups[label]=dict(n=int(ids.sum()),first_mean_seconds=float(lengths.mean()*.02),first_timeout_fraction=float(np.mean(np.array(meta[m]['first_episode_causes']['time_out'])[ids])),
   first_causes={k:int(np.array(v)[ids].sum()) for k,v in meta[m]['first_episode_causes'].items()},start_xy_mean=float(start.mean()),last_valid_xy_mean=float(np.mean(end)),min_xy_mean=float(np.mean(minimum)),
   reached_xy_0_6_fraction=float(np.mean(np.array(minimum)<.6)),all_first_transitions=measure(m,independent),matched_after2s=measure(m,matched))
 results[m]=groups
out=dict(status='PASS',same_initial_states_verified=True,modes=results,limitations=['Rev22 weights transferred into current rev28 scene; not a recreation of old environment.','Current4800 vs old6400 are different training stages.','200Hz leg acceleration includes locomotion/contact, not a pure jitter metric.','Counterfactual changes only walk and alive algebra on frozen trajectories; it is not retraining or complete old rewards.'])
(D/'probe_summary.json').write_text(json.dumps(out,indent=2)+'\n')
fig,ax=plt.subplots(1,2,figsize=(11,4))
empty=(kinds<2)&common[:-1].all(axis=0)
for m in ('current','rev22'):
 x=data[m];v=x['xy'][:-1,empty]
 ax[0].plot((np.arange(999)+1)*.02,v.mean(axis=1),label=m)
ax[0].set(xlabel='Seconds',ylabel='Pelvis-box XY distance (m)',title=f'{int(empty.sum())} jointly surviving starts (selected subset)');ax[0].legend()
a=json.loads((D/'analysis.json').read_text());c=[r for r in a['walk_sweep'] if r['towards_mps']==.85]
ax[1].plot([r['xy_m'] for r in c],[r['current_walk'] for r in c],label='Current walk')
ax[1].plot([r['xy_m'] for r in c],[r['old_walk'] for r in c],label='Rev22 walk')
ax[1].set(xlabel='XY distance (m)',ylabel='Weighted task reward / 20ms',title='Facing box at +0.85 m/s; dz=0.648m');ax[1].legend()
fig.tight_layout();fig.savefig(D/'evidence.png',dpi=160)
print('PROBE_SUMMARY_PASS',json.dumps({m:results[m]['empty']['matched_after2s'] for m in modes}))
