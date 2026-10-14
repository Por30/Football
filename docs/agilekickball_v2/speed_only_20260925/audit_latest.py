from pathlib import Path
import struct,json,statistics
from tensorboard.compat.proto.event_pb2 import Event
p=next(Path('logs/rsl_rl/agilekickball_v2/2026-09-24_15-01-01_stability_fix_scratch').glob('events*'))
start=max(0,p.stat().st_size-30_000_000);data={};count=0
with p.open('rb') as f:
 while True:
  pos=f.tell();header=f.read(12)
  if len(header)<12:break
  size=struct.unpack('<Q',header[:8])[0]
  if size>10_000_000:raise RuntimeError('Invalid event length')
  if pos<start:f.seek(size+4,1);continue
  payload=f.read(size);crc=f.read(4)
  if len(payload)!=size or len(crc)!=4:break
  ev=Event.FromString(payload)
  for v in ev.summary.value:
   if v.HasField('simple_value'):data.setdefault(v.tag,[]).append((ev.step,v.simple_value,ev.wall_time))
  count+=1
end=data['Train/mean_reward'][-1][0];out={}
for k,rows in data.items():
 a=[r for r in rows if end-1000<r[0]<=end];before=[r for r in rows if r[0]<=end-1000]
 if a:out[k]={'mean':statistics.mean(x[1] for x in a),'last':a[-1][1],'count':len(a),'delta':a[-1][1]-before[-1][1] if before else None}
result={'run':str(p.parent),'last_iteration':end,'last_time':max(r[-1][2] for r in data.values()),'window':1000,'metrics':out}
Path('docs/agilekickball_v2/speed_only_20260925/latest_training.json').write_text(json.dumps(result,indent=2))
print('LAST',end)
for k,v in out.items():
 if k.startswith(('Train/','Episode_Termination/','AgileKickball/')) or k in ['AgileV2/speed_upper_m_s','AgileV2/required_hold_mean_s','AgileV2/empirical_mastered_upper_m_s','AgileV2/bin0/joint_success','AgileV2/bin5/joint_success','AgileV2/bin5/served','Loss/aux/encoder_updates','Loss/ball/incoming/velocity_m_s_rmse','Policy/mean_noise_std']:print(k,json.dumps(v))
