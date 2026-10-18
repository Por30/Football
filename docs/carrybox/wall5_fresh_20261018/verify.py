"""Read-only verification after authorized fresh start; waits for actual progress."""
from pathlib import Path
from datetime import datetime
import json,re,time,hashlib,subprocess
import torch
torch.set_num_threads(1)
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
restart=json.loads((OUT/'launch.json').read_text())
PID=restart['pid'];LOG=Path(restart['log'])
RUN=None
for _ in range(100):
    assert Path(f'/proc/{PID}/cmdline').exists(),'Formal process exited'
    candidates=list(LOG.parent.glob('*_'+restart['run_name']))
    if candidates:RUN=candidates[0]
    text=LOG.read_text(errors='replace')
    assert not re.search(r'Traceback \(most recent call last\)|CUDA error:|OutOfMemoryError|FloatingPointError',text)
    completed=re.findall(r'Iteration time:\s*([\d.]+)s',text)
    if RUN is not None and len(completed)>=12:break
    time.sleep(10)
else:raise TimeoutError('Formal training did not reach 12 iterations')

def rows():
    text=re.sub(r'\x1b\[[0-9;]*m','',LOG.read_text(errors='replace'))
    assert not re.search(r'Traceback \(most recent call last\)|CUDA error:|OutOfMemoryError|FloatingPointError',text)
    blocks=re.split(r'Learning iteration (\d+)/40000',text)
    result=[]
    for i in range(1,len(blocks),2):
        body=blocks[i+1]
        def value(pattern):
            match=re.search(pattern,body);return float(match[1]) if match else None
        elapsed=value(r'Iteration time:\s*([\d.]+)s')
        if elapsed is not None:
            result.append(dict(iteration=int(blocks[i]),seconds=elapsed,
                episode_steps=value(r'Mean episode length:\s*([-\d.]+)'),
                box_position_loss=value(r'Mean box_position loss:\s*([-\d.]+)'),
                style_reward=value(r'AMP/style_reward:\s*([-\d.]+)'),
                amp_valid_fraction=value(r'AMP/valid_fraction:\s*([-\d.]+)')))
    return result

start=rows();assert start
assert 'Loading model checkpoint from:' not in LOG.read_text(errors='replace')
assert not any('--resume' in x or '--checkpoint' in x or '--warm_start' in x for x in restart['command'])
assert re.search(r'^resume: false$',(RUN/'params/agent.yaml').read_text(),re.M)
for path,digest in json.loads((OUT.parent/'wall5_perf_20261018/unchanged_scope.json').read_text()).items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
state=torch.load(RUN/'model_0.pt',map_location='cpu',weights_only=False)
contract=state['environment_contract'];assert state['carrybox_schema']==2
assert contract['migration_revision']==13 and contract['amp_shape']==[10,60]
assert contract['reset_probs']==[.8,0.,.2] and contract['held_box_reference_reset']
amp=state['amp'];assert amp['config']['schema']==3 and amp['config']['frame_dim']==60
assert amp['dataset']['clip_count']==13 and amp['statistics_initialized']
assert state['pose_aux_coef']==.1 and amp['config']['ppo']['schedule']=='adaptive'
assert amp['config']['ppo']['epochs']==5 and amp['config']['ppo']['mini_batches']==4
assert int(amp['model']['running_count'])==61440,amp['model']['running_count']
assert int(state['iter'])==0
for model in (state['model_state_dict'],amp['model']):assert all(torch.isfinite(v).all() for v in model.values())
for opt in (state['optimizer_state_dict'],amp['optimizer']):
    assert opt['state']
    assert {float(x['step']) for x in opt['state'].values()}=={20.},'optimizer was not freshly initialized'
    for entry in opt['state'].values():
        for value in entry.values():
            if isinstance(value,torch.Tensor):assert torch.isfinite(value).all()
# Ensure completed iterations, not just an alive process or a growing startup log.
time.sleep(12)
end=rows();assert end[-1]['iteration']>start[-1]['iteration']
command=Path(f'/proc/{PID}/cmdline').read_bytes().replace(b'\0',b' ').decode()
assert '--task Template-Perceptual-Ball-CarryBox-Walled5-v0' in command and '--num_envs 4096' in command
assert '--resume' not in command and '--checkpoint' not in command and '--warm_start' not in command
warm=end[2:][-10:];assert warm
assert sum(x['seconds'] for x in warm)/len(warm)<6.,warm
result=dict(status='PASS',checked_at=datetime.now().astimezone().isoformat(timespec='seconds'),pid=PID,command=command,
    run=str(RUN),log=str(LOG),progress_from=start[-1]['iteration'],progress_to=end[-1]['iteration'],
    recent_iterations=warm,mean_iteration_seconds=sum(x['seconds'] for x in warm)/len(warm),max_iteration_seconds=max(x['seconds'] for x in warm),
    checkpoint=str(RUN/'model_0.pt'),environment_contract=contract,amp_config=amp['config'],amp_dataset=amp['dataset'],
    finite_policy_and_amp=True,finite_nonempty_optimizers=True,normalizer_count=float(amp['model']['running_count']),
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,memory.free,utilization.gpu','--format=csv,noheader'],text=True).strip(),
    convergence='not_evaluated',process_modified=True,initialization='fresh',loaded_checkpoint=None,first_checkpoint_optimizer_steps=20)
(OUT/'snapshot.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','checked_at','pid','progress_from','progress_to','mean_iteration_seconds','max_iteration_seconds')},ensure_ascii=False))
