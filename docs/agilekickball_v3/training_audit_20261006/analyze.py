"""Retrospective diagnostics of two single-seed runs; no causal efficacy claim."""
from pathlib import Path
import datetime
import hashlib
import json
from zoneinfo import ZoneInfo
import numpy as np
import torch
from tensorboard.backend.event_processing.event_file_loader import RawEventFileLoader
from tensorboard.compat.proto.event_pb2 import Event

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
RUNS={
 'v2':ROOT/'logs/rsl_rl/agilekickball_v2/2026-09-25_22-18-55_v1_speed_only_20260925_scratch',
 'v3':ROOT/'logs/rsl_rl/agilekickball_v3/2026-10-03_23-56-27_contact_outcome_20261003_scratch',
}
all_data={}
report={'analysis_kind':'retrospective training-log diagnostics, not matched-distribution evaluation',
 'analysis_date':'2026-10-06','independent_training_seeds_per_condition':1,
 'window_mean_definition':'unweighted arithmetic mean of logged iteration scalars; not pooled trial success',
 'confounds':['serve distance ceiling 2->3 m','lateral aim half-width .25->.35 m','robot travel radius .6->1.2 m','ball end radius 3->4 m','adaptive speed distributions differ','outcome auxiliary enabled only in v3'],
 'runs':{}}
for name,path in RUNS.items():
 data={}; wall=np.full(50000,np.nan)
 files=sorted(path.glob('events.out.tfevents.*'))
 for file in files:
  for record in RawEventFileLoader(str(file)).Load():
   event=Event.FromString(record)
   step=event.step
   if not 0<=step<50000:continue
   for value in event.summary.value:
    tag=value.tag
    if tag.endswith('/time') or not value.HasField('simple_value'):continue
    if tag not in data:data[tag]=np.full(50000,np.nan)
    data[tag][step]=value.simple_value
    wall[step]=event.wall_time
 all_data[name]=data
 means={}
 for label,start,end in [('first1000',0,1000),('last1000',49000,50000)]+[(f'ending_{end}',max(0,end-1000),end) for end in (5000,10000,20000,30000,40000,45000,48000)]:
  means[label]={k:float(np.nanmean(v[start:end])) for k,v in data.items() if np.isfinite(v[start:end]).any()}
 stage=f'Agile{name.upper()}/'
 thresholds={}
 for key,threshold in [('extension_unlocked',.5),('course_upper_m_s',2),('course_upper_m_s',3),('course_upper_m_s',6)]:
  v=data[stage+key];ids=np.flatnonzero(v>=threshold-1e-6)
  thresholds[f'{key}>={threshold}']=int(ids[0]) if len(ids) else None
 checkpoints={}
 for filename in ('model_0.pt','model_49999.pt'):
  p=path/filename
  ck=torch.load(p,weights_only=False,map_location='cpu')
  key='agile_v2_recovery_curriculum' if name=='v2' else 'agile_v3_wide_serve_curriculum'
  info={'iter':ck['iter'],'finite_model':all(torch.isfinite(v).all().item() for v in ck['model_state_dict'].values()),
        'curriculum':ck[key],'modified_jst':datetime.datetime.fromtimestamp(p.stat().st_mtime,ZoneInfo('Asia/Tokyo')).isoformat(),
        'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  if name=='v3':
   aux=ck['contact_outcome'];ids=aux['optimizer']['param_groups'][0]['params']
   info['outcome_config']=aux['config']
   info['outcome_optimizer_step_counts']=[float(aux['optimizer']['state'][i]['step']) for i in ids]
   heads=torch.cat([v.flatten() for k,v in ck['model_state_dict'].items() if k.startswith('outcome_head.')])
   if filename=='model_0.pt':initial_heads=heads
   else:
    info['outcome_head_l2_change_vs_first_checkpoint']=float((heads-initial_heads).norm())
    info['outcome_head_relative_l2_change_vs_first_checkpoint']=float((heads-initial_heads).norm()/initial_heads.norm())
  checkpoints[filename]=info
 integrity={k:int((~np.isfinite(v)).sum()) for k,v in data.items() if k.startswith('Loss/outcome/') or k in ('Train/mean_episode_length','Train/mean_reward')}
 report['runs'][name]={'path':str(path),'event_files':[str(p) for p in files],
  'logged_iterations':int(np.isfinite(data[stage+'course_upper_m_s']).sum()),
  'first_event_jst':datetime.datetime.fromtimestamp(float(wall[np.isfinite(wall)][0]),ZoneInfo('Asia/Tokyo')).isoformat(),
  'last_event_jst':datetime.datetime.fromtimestamp(float(wall[np.isfinite(wall)][-1]),ZoneInfo('Asia/Tokyo')).isoformat(),
  'window_means':means,'milestones':thresholds,'last':{k:float(v[np.isfinite(v)][-1]) for k,v in data.items() if np.isfinite(v).any()},
  'checkpoints':checkpoints,'missing_or_nonfinite_scalar_counts':integrity}
 if name=='v3':
  report['runs'][name]['outcome_total_encoder_updates']=float(data['Loss/outcome/encoder_updates'].sum())
  report['runs'][name]['outcome_total_head_only_batches']=float(data['Loss/outcome/head_only_batches'].sum())
  report['runs'][name]['outcome_max_stage_kl']=float(data['Loss/outcome/stage_monitor_kl'].max())
 print(name,'read',len(data),'tags;',thresholds,flush=True)
(OUT/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
np.savez_compressed(OUT/'scalars.npz',**{name+'::'+tag:v for name,data in all_data.items() for tag,v in data.items()})
# Logged last-termination-type proportions are maintained per environment, not
# fresh incident counts. Retain them as diagnostics, not empirical failure rates.
keys=['Train/mean_reward','Train/mean_episode_length','Episode_Termination/recovery_timeout','Episode_Termination/walked_away','Episode_Termination/time_out','Loss/ball/visible/position_cm_rmse','Loss/ball/incoming/position_cm_rmse','Loss/ball/visible/fraction']
for name,result in report['runs'].items():
 means=result['window_means']['last1000']
 print(name,'LAST1000',json.dumps({k:means.get(k) for k in keys}),flush=True)
 print(name,'COURSE',json.dumps({k:v for k,v in means.items() if k.startswith(f'Agile{name.upper()}/')}),flush=True)
 if name=='v3':
  for window in ('first1000','last1000'):
   print('v3',window,'OUTCOME',json.dumps({k:v for k,v in result['window_means'][window].items() if k.startswith('Loss/outcome/')}),flush=True)
