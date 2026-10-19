"""Launch the explicitly authorized fresh run once, only after all prerequisite receipts pass."""
from datetime import datetime
from pathlib import Path
import hashlib,json,re,subprocess,time
import torch
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2];torch.set_num_threads(1)
for stage in ('check','smoke'):
    receipts=json.loads((DOC/f'receipts_{stage}.json').read_text())
    assert receipts['tests'] and all(t['result']=='PASS' for t in receipts['tests']),f'{stage} is not PASS: formal launch blocked'
assert json.loads((DOC/'physical.json').read_text())['status']=='PASS'
assert json.loads((DOC/'pilot.json').read_text())['status']=='PASS'

if (DOC/'launch.json').exists():
    record=json.loads((DOC/'launch.json').read_text())
    assert Path(f'/proc/{record["pid"]}/cmdline').exists(),'Previously launched process exited; do not launch twice'
else:
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:args=proc.joinpath('cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError,PermissionError,ProcessLookupError):continue
        if b'scripts/rsl_rl/train.py' in args:raise RuntimeError('Another training process exists: '+proc.name)
    free=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits','-i','0'],text=True).strip())
    assert free>19000,free
    name='wall5_v16_loco_fix_fresh_'+datetime.now().strftime('%Y%m%d_%H%M%S')
    log=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5'/('launch_'+name+'.log')
    command=['/home/cao/ENTER/envs/ball/bin/python','-u','scripts/rsl_rl/train.py','--task','Template-Perceptual-Ball-CarryBox-Walled5-v0',
             '--num_envs','4096','--device','cuda:0','--headless','--seed','42','--max_iterations','40000','--run_name',name]
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in json.loads((DOC/'before_hashes.json').read_text())}
    with log.open('x') as stream:
        proc=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    record=dict(pid=proc.pid,log=str(log),command=command,run_name=name,initialization='fresh',loaded_checkpoint=None,
                started_at=datetime.now().astimezone().isoformat(),free_mib=free,source_sha256=hashes)
    (DOC/'launch.json').write_text(json.dumps(record,indent=2)+'\n');print('FORMAL_LAUNCHED',json.dumps(record),flush=True)

start=time.monotonic();first=None
while time.monotonic()-start<600:
    command=[x.decode() for x in Path(f'/proc/{record["pid"]}/cmdline').read_bytes().split(b'\0') if x]
    assert command==record['command']
    log=Path(record['log']).read_text()
    assert not re.search(r'Traceback \(most recent call last\)|CUDA error:|out of memory|illegal memory access',log)
    iterations=[int(x) for x in re.findall(r'Learning iteration (\d+)/40000',log)]
    times=[float(x) for x in re.findall(r'Iteration time:\s*([\d.]+)s',log)]
    if iterations and first is None:first=iterations[-1]
    if len(times)>=16 and iterations[-1]>=max(15,(first or 0)+2):break
    print('WAIT',datetime.now().astimezone().isoformat(),iterations[-1] if iterations else 'startup',flush=True)
    time.sleep(15)
else:raise RuntimeError('Formal launch did not complete required iterations')

runs=list((ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5').glob('*_'+record['run_name']));assert len(runs)==1
run=runs[0];model=torch.load(run/'model_0.pt',map_location='cpu',weights_only=False)
c=model['environment_contract'];assert model['carrybox_schema']==2 and c['migration_revision']==16
assert c['reset_probs']==[.8,0.,.2] and c['reset_assignment']=='fixed_env_midpoint_skill_quota_v1'
assert c['critic_shape']==108 and c['actor_observations']=='proprio93x4_depth4x27x48_no_privileged'
assert c['actuator_gains']['feet']==dict(stiffness=200.,damping=5.,effort_limit_sim=35.,velocity_limit_sim=30.)
assert c['default_joint_pose']['.*_hip_pitch_joint']==-.18 and c['default_joint_pose']['.*_ankle_pitch_joint']==-.12
assert model['amp']['dataset']['clip_count']==13 and model['amp']['config']['frame_dim']==60
assert model['amp']['config']['action_regularization']['max_std']==1.
for collection in (model['model_state_dict'],model['amp']['model']):assert all(torch.isfinite(v).all() for v in collection.values())
for optimizer in (model['optimizer_state_dict'],model['amp']['optimizer']):
    assert {int(v['step']) for v in optimizer['state'].values()}=={20}
    assert all(torch.isfinite(x).all() for v in optimizer['state'].values() for x in v.values() if isinstance(x,torch.Tensor))
assert model['model_state_dict']['log_std'].exp().max()<=1.
assert 'Sampling/loco_transition_fraction: 0.8000' in log and 'Sampling/hold_transition_fraction: 0.2000' in log
warm=times[-10:];assert max(warm)<=6.,warm
snapshot=dict(status='PASS',pid=record['pid'],run=str(run),log=record['log'],checked_at=datetime.now().astimezone().isoformat(),
              initialization='fresh',loaded_checkpoint=None,progress_from=first,progress_to=iterations[-1],
              mean_iteration_seconds=sum(warm)/len(warm),max_iteration_seconds=max(warm),
              checkpoint=str(run/'model_0.pt'),revision=16,amp_clips=13,actor_privileged=False,critic_dim=108,
              skill_environment_counts=[3277,0,819],optimizer_updates_verified=True,convergence_evaluated=False)
(DOC/'snapshot.json').write_text(json.dumps(snapshot,indent=2)+'\n');print('FORMAL_START_PASS',json.dumps(snapshot),flush=True)
