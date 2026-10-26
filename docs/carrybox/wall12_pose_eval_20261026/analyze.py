import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path
from datetime import datetime
import torch
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
from metrics import measurements, summarize

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
RUN=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled12/2026-10-25_12-32-53_wall12_24step_pose_aux_fresh_20261025_123249'
MODEL=RUN/'model_19999.pt'
torch.set_num_threads(1)
state=torch.load(MODEL,map_location='cpu',weights_only=False)
assert state['carrybox_schema']==2 and state['iter']==19999
assert state['environment_contract']['variant']=='walled12' and state['pose_aux_coef']==1.
assert state['environment_contract']['pose_supervision']['prediction_dim']==9
assert all(torch.isfinite(v).all() for v in state['model_state_dict'].values())
assert all(torch.isfinite(v).all() for v in state['amp']['model'].values())
events=EventAccumulator(str(RUN),size_guidance={'scalars':0});events.Reload()
stats={}
for tag in ('Loss/pose_position','Loss/pose_rotation','Loss/pose_aux_weighted','Loss/pose_samples'):
    rows=events.Scalars(tag); assert len(rows)==20000 and rows[-1].step==19999
    assert all(math.isfinite(r.value) for r in rows)
    stats[tag]=dict(first=rows[0].value,last=rows[-1].value,
        windows={str(n):sum(r.value for r in rows[-n:])/n for n in (100,1000)},
        first100=sum(r.value for r in rows[:100])/100,
        milestones={str(i):rows[i].value for i in (0,1000,5000,10000,15000,19999)})
position=stats['Loss/pose_position']['windows']['1000']
stats['position_rms_from_last1000']=dict(per_coordinate_cm=math.sqrt(position)*100,
    euclidean_rmse_cm=math.sqrt(3*position)*100,meaning='training residuals aggregated across optimizer minibatches, not fixed-model evaluation')
log=(RUN.parent/'train_wall12_24step_pose_aux_fresh_20261025_123249.log').read_text(errors='replace')
iterations=re.findall(r'Learning iteration (\d+)/20000',log)
assert len(iterations)==20000 and int(iterations[-1])==19999
assert 'Traceback (most recent call last)' not in log
active=[]
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:args=p.joinpath('cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError,ProcessLookupError,PermissionError):continue
    if b'scripts/rsl_rl/train.py' in args:active.append(int(p.name))
assert not active,active
spec=importlib.util.spec_from_file_location('pose',ROOT/'source/perceptual_ball/perceptual_ball/carrybox_wall12.py')
pose=importlib.util.module_from_spec(spec);spec.loader.exec_module(pose)
s=pose.box_rotations(torch.device('cpu'),torch.float64)
target=torch.tensor([[0.,0.,1.,1.,0.,0.,0.,1.,0.,.30,.30,.25]],dtype=torch.float64)
prediction=target[:,:9].clone(); prediction[:,0]=.03;prediction[:,1]=.04
m=measurements(prediction,target,s,pose.box_symmetry_mask(target[:,9:],s))
assert abs(float(m['position_m'])-.05)<1.e-12 and float(m['angle_deg'])<1.e-6
prediction[:,3:]=torch.tensor([0.,1.,0.,-1.,0.,0.])
m=measurements(prediction,target,s,pose.box_symmetry_mask(target[:,9:],s));assert float(m['angle_deg'])<1.e-6
assert abs(float(m['raw_angle_deg'])-90)<1.e-6
target[:,9]=.21
m=measurements(prediction,target,s,pose.box_symmetry_mask(target[:,9:],s));assert abs(float(m['angle_deg'])-90)<1.e-6
prediction[:,3:]=0
m=measurements(prediction,target,s,pose.box_symmetry_mask(target[:,9:],s));assert not m['angle_valid'].any()
report=dict(checked_at=datetime.now().astimezone().isoformat(),checkpoint=str(MODEL),
    checkpoint_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),checkpoint_iter=state['iter'],
    training_completed=True,active_training_pids=active,stop_action='none_already_exited',
    contract=state['environment_contract'],losses=stats,metric_synthetic_checks=True)
(OUT/'training_analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(losses=stats,training_completed=True,metric_checks='PASS'),ensure_ascii=False,indent=2))
