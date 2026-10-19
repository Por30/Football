"""Read-only check of the newly authorized formal run, not a convergence evaluation."""
from pathlib import Path
from datetime import datetime
import json,re,time,torch
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2];torch.set_num_threads(1)
s=json.loads((DOC/'launch.json').read_text());pid=s['pid'];start=time.monotonic();first=None
assert s['initialization']=='fresh' and not any(x in s['command'] for x in ('--resume','--checkpoint','--carrybox_warm_start'))
def status():
    command=[x.decode() for x in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if x]
    assert command==s['command']
    text=Path(s['log']).read_text();assert not re.search(r'Traceback \(most recent call last\)|CUDA error:|out of memory|illegal memory access',text)
    iterations=[int(x) for x in re.findall(r'Learning iteration (\d+)/40000',text)]
    times=[float(x) for x in re.findall(r'Iteration time:\s*([\d.]+)s',text)]
    return iterations,times,text
while time.monotonic()-start<900:
    iterations,times,log=status()
    if iterations and first is None:first=iterations[-1]
    if len(times)>=13 and iterations[-1]>=max(12,(first or 0)+2):break
    print('WAIT',datetime.now().astimezone().isoformat(),iterations[-1] if iterations else 'startup',flush=True);time.sleep(15)
else:raise RuntimeError('Formal run did not complete enough iterations')
runs=list((ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5').glob('*_'+s['run_name']));assert len(runs)==1
run=runs[0];model=torch.load(run/'model_0.pt',map_location='cpu',weights_only=False)
c=model['environment_contract'];assert model['carrybox_schema']==2 and c['migration_revision']==14 and c['critic_shape']==108
assert c['reset_probs']==[.8,0.,.2] and c['amp_shape']==[10,60]
assert c['actor_observations']=='proprio93x4_depth4x27x48_no_privileged'
state=model['model_state_dict']
critic=[v for k,v in state.items() if k.startswith('critic.') and k.endswith('weight') and v.ndim==2]
actor=[v for k,v in state.items() if k.startswith('actor.') and k.endswith('weight') and v.ndim==2]
assert critic[0].shape==(512,108) and actor[0].shape==(512,500)
for collection in (state,model['amp']['model']):assert all(torch.isfinite(v).all() for v in collection.values())
for optimizer in (model['optimizer_state_dict'],model['amp']['optimizer']):
    steps={int(v['step']) for v in optimizer['state'].values()};assert steps=={20},steps
    assert all(torch.isfinite(x).all() for v in optimizer['state'].values() for x in v.values() if isinstance(x,torch.Tensor))
assert model['amp']['dataset']['clip_count']==13 and model['amp']['config']['frame_dim']==60
normalizer_count=int(model['amp']['model']['running_count']);assert normalizer_count==61440,normalizer_count
agent=(run/'params/agent.yaml').read_text();assert 'resume: false' in agent and 'class_name: CarryBoxWall5ActorCritic' in agent
warm=times[-10:];assert max(warm)<6.,warm
result=dict(status='PASS',checked_at=datetime.now().astimezone().isoformat(),pid=pid,run=str(run),log=s['log'],
            initialization='fresh',loaded_checkpoint=None,revision=14,actor_input=[372,4,27,48],critic_dim=108,
            progress_from=first,progress_to=iterations[-1],mean_iteration_seconds=sum(warm)/len(warm),max_iteration_seconds=max(warm),
            initial_optimizer_steps=20,initial_amp_normalizer_count=normalizer_count,
            checkpoint=str(run/'model_0.pt'),finite_parameters_and_optimizers=True,
            amp_clips=13,amp_frame_dim=60,rsi=[.8,0.,.2],convergence_evaluated=False)
(DOC/'snapshot.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
