"""Verify advancing 4096 fresh training and the exact validated task contract."""
from pathlib import Path
from datetime import datetime
import json,re,time,hashlib,torch
D=Path(__file__).resolve().parent;R=D.parents[2];r=json.loads((D/'launch.json').read_text());torch.set_num_threads(1)
assert r['initialization']=='fresh' and r['loaded_checkpoint'] is None
assert not any(a.startswith(('--resume','--checkpoint','--warm_start')) for a in r['command'])
first=None
for _ in range(60):
 cmd=[a.decode() for a in Path(f'/proc/{r["pid"]}/cmdline').read_bytes().split(b'\0') if a]
 assert cmd==r['command']
 log=Path(r['log']).read_text()
 assert not re.search(r'Traceback \(most recent call last\)|PhysX error|CUDA error:|out of memory|illegal memory access',log)
 iterations=[int(x) for x in re.findall(r'Learning iteration (\d+)/40000',log)]
 times=[float(x) for x in re.findall(r'Iteration time:\s*([\d.]+)s',log)]
 if iterations and first is None:first=iterations[-1]
 if len(times)>=16 and iterations[-1]>=max(15,(first or 0)+10):break
 print('WAIT',iterations[-1] if iterations else 'startup',flush=True);time.sleep(15)
else:raise RuntimeError('Startup did not progress within 900s')
runs=list((R/'logs/rsl_rl/g1_carrybox_depth/walled5').glob('*_'+r['run_name']));assert len(runs)==1
run=runs[0];m=torch.load(run/'model_0.pt',map_location='cpu',weights_only=False);c=m['environment_contract']
assert json.loads(json.dumps(c))==json.loads((D/'smoke.json').read_text())['contract']
assert m['carrybox_schema']==2 and c['migration_revision']==25
assert c['reset_default_probability']==.2 and c['reset_reference_probability']==.8
assert c['termination_profile']['roll_rad'] is None and c['termination_profile']['pitch_rad'] is None
assert c['roll_limit'] is None
assert 'Episode_Termination/tipped' not in log
assert 'Skill/loco_tilt_at_episode_end_fraction' in log
assert c['self_collisions'] and c['self_collision_filter_pairs']==[]
assert c['physics_action_delay']['range_s']==[0.,.02] and c['support_platform']
assert 'undesired_contacts' not in c['reward_weights']
assert c['critic_shape']==123 and c['amp_shape']==[10,60]
assert m['amp']['dataset']['clip_count']==15 and m['amp']['config']['frame_dim']==60
assert int(m['amp']['model']['running_count'])==61440
for collection in (m['model_state_dict'],m['amp']['model']):assert all(torch.isfinite(v).all() for v in collection.values())
for opt in (m['optimizer_state_dict'],m['amp']['optimizer']):
 assert {int(v['step']) for v in opt['state'].values()}=={20}
 assert all(torch.isfinite(x).all() for v in opt['state'].values() for x in v.values() if isinstance(x,torch.Tensor))
assert 'resume: false' in (run/'params/agent.yaml').read_text()
assert re.search(r'\bnum_envs:\s*4096\b',(run/'params/env.yaml').read_text())
metrics={}
for key in ('Reset/default_fraction','Reset/loco_rsi_fraction','Reset/pickup_rsi_fraction','Reset/hold_rsi_fraction','Mean episode length','Skill/loco_mean_steps','Skill/pickup_mean_steps','Skill/hold_mean_steps','AMP/style_reward','Reward/amp_per_step'):
 values=re.findall(re.escape(key)+r':\s*([-+\d.eE]+)',log)
 assert values,key
 metrics[key]=float(values[-1])
for key,target in [('default',.2),('loco_rsi',8/15),('pickup_rsi',2/15),('hold_rsi',2/15)]:
 assert abs(metrics['Reset/'+key+'_fraction']-target)<.025
for name,h in r['source_sha256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h,name
old=Path(f"/proc/{json.loads((D/'stopped_run.json').read_text())['pid']}/cmdline");assert not old.exists() or not old.read_bytes()
warm=times[-10:];assert max(warm)<=6.,warm
result=dict(status='PASS',checked_at=datetime.now().astimezone().isoformat(),pid=r['pid'],run=str(run),log=r['log'],checkpoint=str(run/'model_0.pt'),revision=25,num_envs=4096,initialization='fresh',iteration=iterations[-1],progress_from=first,mean_iteration_seconds=sum(warm)/len(warm),max_iteration_seconds=max(warm),metrics=metrics,finite_parameters=True,initial_optimizer_step=20,convergence_evaluated=False)
(D/'snapshot.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
