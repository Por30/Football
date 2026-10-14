"""Read-only retrospective console-log audit; rounded scalars, no causal claim."""
import datetime,json,re
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
RUN=ROOT/'logs/rsl_rl/agilekickball_v3/2026-10-08_11-48-24_feedback_stable_20261008_v2init'
log=ROOT/'logs/background/agilekickball_v3_feedback_stable_20261008_114819.log'
data={};step=-1
iteration=re.compile(r'Learning iteration\s+(\d+)/50000')
with log.open() as stream:
 for line in stream:
  if 'Learning iteration' in line:
   match=iteration.search(line)
   if match:step=int(match[1])
   continue
  if step<0:continue
  key,sep,value=line.rpartition(':');key=key.strip()
  if key=='Mean reward':tag='Train/mean_reward'
  elif key=='Mean episode length':tag='Train/mean_episode_length'
  elif key=='Mean action noise std':tag='Policy/mean_noise_std'
  elif key.startswith('Mean ') and key.endswith(' loss'):tag='Loss/'+key[5:-5]
  elif key.startswith(('AgileV3/','AgileKickball/','Episode_Termination/','Episode_Reward/','AMP/')):tag=key
  else:continue
  try:v=float(value)
  except ValueError:continue
  if tag not in data:data[tag]=np.full(50000,np.nan)
  data[tag][step]=v
windows={}
for end in (1000,5000,10000,15000,20000,30000,40000,45000,48000,50000):
 windows[f'ending_{end}']={k:float(np.nanmean(v[end-1000:end])) for k,v in data.items() if np.isfinite(v[end-1000:end]).any()}
milestones={}
for key,threshold in [('extension_unlocked',.5),('course_upper_m_s',2),('course_upper_m_s',4),('course_upper_m_s',6)]:
 ids=np.flatnonzero(data['AgileV3/'+key]>=threshold)
 milestones[key+'>='+str(threshold)]=int(ids[0]) if len(ids) else None
state=torch.load(RUN/'model_49999.pt',map_location='cpu',weights_only=False)
old=json.loads((ROOT/'docs/agilekickball_v3/stability_fix_20261008/comparison.json').read_text())
report=dict(run_dir=str(RUN),log=str(log),iterations=len(np.flatnonzero(np.isfinite(data['Train/mean_episode_length']))),
 revision=state['agile_v3_state_feedback_curriculum']['config']['revision'],
 completed_jst=datetime.datetime.fromtimestamp((RUN/'model_49999.pt').stat().st_mtime,ZoneInfo('Asia/Tokyo')).isoformat(),
 finite_checkpoint=all(torch.isfinite(v).all().item() for v in state['model_state_dict'].values()),
 current=dict(last1000=windows['ending_50000'],window_means=windows,milestones_from_rounded_console=milestones,
              course=state['agile_v3_state_feedback_curriculum'],state_feedback=state['state_feedback'],initialization=state['initialization']),
 v2_last1000=old['runs']['v2']['window_means']['last1000'],failed_v3_last1000=old['runs']['v3']['window_means']['last1000'],
 limitations=['Current console scalars rounded to printed precision; cached v2/failed v3 from TensorBoard.',
              'Episode length raw units are control steps, multiply by .02 seconds.',
              'Training window means are not pooled independent episode success rates.',
              'Termination log scalars are last recorded type per environment, not fresh event incidence.',
              'Current v3 used v2 initialization; training curves do not isolate module efficacy.'])
(OUT/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
np.savez_compressed(OUT/'scalars.npz',**data)
keys=['Train/mean_reward','Train/mean_episode_length','Loss/ball/visible/position_cm_rmse','Loss/ball/incoming/position_cm_rmse','Loss/ball/visible/velocity_m_s_rmse']
for label,values,prefix in [('v2',report['v2_last1000'],'AgileV2/'),('failed_v3',report['failed_v3_last1000'],'AgileV3/'),('current_v3',windows['ending_50000'],'AgileV3/')]:
 print(label,{k:values[k] for k in keys+[prefix+'recent_recovered_serve_share',prefix+'recent_kick_proxy_share',prefix+'course_upper_m_s']})
print('MILESTONES',milestones)
print('WINDOWS', {k:{field:v[field] for field in ['Train/mean_episode_length','Train/mean_reward','AgileV3/recent_recovered_serve_share','AgileV3/course_upper_m_s']} for k,v in windows.items()})
print('MODULE',{k:v for k,v in windows['ending_50000'].items() if k.startswith(('Loss/state_feedback/','Loss/aux/'))})
