"""Summarize first episodes, preserving failure, timeout and censoring denominators."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import statistics as st
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DOC=Path(__file__).resolve().parent; ROOT=DOC.parents[2]
selection=json.loads((DOC/'selection.json').read_text())
result=dict(status='PASS',checkpoint=selection['checkpoint'],checkpoint_sha256=selection['checkpoint_sha256'],
            checked_at=datetime.now().astimezone().isoformat(),cases={})
fig,axes=plt.subplots(1,2,figsize=(11,4.5),constrained_layout=True)
for mode in ('mean','sample'):
    data=json.loads((DOC/f'{mode}.json').read_text())
    assert data['status']=='PASS' and data['checkpoint_sha256']==selection['checkpoint_sha256']
    assert data['policy_parameters_unchanged'] and data['training_updates']==0
    if mode=='sample':assert data['initial_states_checked']
    episodes=data['first_episodes'];assert len(episodes)==32
    failed=[e for e in episodes if e['failure']]
    completed=[e for e in episodes if not e['censored']]
    survived=lambda steps:sum(e['steps']>steps or (e['steps']==steps and not e['failure']) for e in episodes)
    survivors=[e for e in episodes if e['steps']==1000 and not e['failure']]
    row=dict(num_first_episodes=32,executed_steps=data['executed_steps'],
        survival_counts={str(sec)+'s':survived(sec*50) for sec in (1,5,10,20)},
        failures=len(failed),natural_timeouts=sum(e['time_out'] for e in episodes),
        censored=sum(e['censored'] for e in episodes),
        mean_completed_steps=st.mean(e['steps'] for e in completed) if completed else None,
        median_failure_seconds=st.median(e['seconds'] for e in failed) if failed else None,
        failure_seconds_range=[min(e['seconds'] for e in failed),max(e['seconds'] for e in failed)] if failed else None,
        tipped=sum(e['tipped'] for e in episodes),fell=sum(e['fell'] for e in episodes),invalid=sum(e['invalid'] for e in episodes),
        terminal_roll_over_limit=sum(e['failure'] and abs(e['roll'])>.5 for e in episodes),
        terminal_pitch_over_limit=sum(e['failure'] and abs(e['pitch'])>1.1 for e in episodes),
        failures_before_first_push=sum(e['failure'] and e['push_count']==0 for e in episodes),
        lift_successes=sum(e['success'] for e in episodes),
        median_first_episode_displacement_xy=st.median(e['displacement_xy'] for e in episodes),
        median_first_episode_towards_initial_box=st.median(e['towards_initial_box'] for e in episodes),
        median_box_distance_reduction=st.median(e['box_distance_start']-e['box_distance_end'] for e in episodes),
        survivors_20s=survivors,
        initial_roll_range=[min(data['initial']['roll']),max(data['initial']['roll'])],
        initial_pitch_range=[min(data['initial']['pitch']),max(data['initial']['pitch'])])
    foot_evidence=[]
    for e,trajectory in zip(episodes,data['trajectories']):
        assert len(trajectory)==e['steps']
        root=np.array([f['root'] for f in trajectory]);feet=np.array([f['feet'] for f in trajectory])
        force=np.array([f['foot_force'] for f in trajectory]);initial=np.array(data['initial']['feet'][e['env']])
        relative=feet-root[:,None,:]
        foot_evidence.append(dict(env=e['env'],first_episode_steps=e['steps'],
            foot_world_xy_range_m=np.ptp(np.concatenate((initial[None,:,:2],feet[:,:,:2])),axis=0).tolist(),
            foot_relative_xy_range_m=np.ptp(relative[:,:,:2],axis=0).tolist(),
            foot_contact_transitions_gt10N=np.sum(np.diff((force>10).astype(int),axis=0)!=0,axis=0).tolist(),
            survived_20s=e['steps']==1000 and not e['failure']))
    row['foot_evidence']=foot_evidence
    result['cases'][mode]=row
    times=np.linspace(0,20,1001)
    axes[0].step(times,[survived(round(t*50)) for t in times],where='post',label=mode)
    axes[1].scatter([e['seconds'] for e in episodes],[e['towards_initial_box'] for e in episodes],label=mode,alpha=.65)
command=[a.decode() for a in Path(f'/proc/{selection["training_pid"]}/cmdline').read_bytes().split(b'\0') if a]
assert command==selection['training_command']
for name,digest in selection['source_sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
assert hashlib.sha256(Path(selection['checkpoint']).read_bytes()).hexdigest()==selection['checkpoint_sha256']
result.update(training_pid=selection['training_pid'],training_process_unchanged=True,production_source_unchanged=True,
    initial_states_and_actor_observations_matched=True,
    limits=['32 first episodes per action mode, one reset seed: bounded checkpoint diagnosis, not deployment validation',
            'Displacement includes initial RSI momentum; foot motion/contact alone does not prove controlled gait',
            'Terminal classifications may overlap; timeout and failure are independently reported',
            'Concurrent replay temporarily shares the training GPU; rollout FPS is not a training benchmark'])
axes[0].set(xlabel='Time (s)',ylabel='First episodes alive (of 32)',ylim=(-.5,32.5),title='Loco-only first-episode survival')
axes[1].axhline(0,color='gray',lw=1)
axes[1].set(xlabel='First episode duration (s)',ylabel='Motion toward initial box (m)',title='Motion before first reset; includes RSI inertia')
for ax in axes:ax.legend();ax.grid(alpha=.25)
fig.savefig(DOC/'loco_survival.png',dpi=150);plt.close(fig)
(DOC/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:{kk:vv for kk,vv in v.items() if kk!='foot_evidence'} for k,v in result['cases'].items()},indent=2))
