"""Read-only verification of the user's wall5 launch; no CUDA tensors or simulation."""
from pathlib import Path
from datetime import datetime
import json,re,time,hashlib,subprocess
import torch
torch.set_num_threads(1)
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
PID=3804340
RUN=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-18_12-27-37_wall5_v13_hold_rsi'
LOG=RUN.parent/'launch_v13_20261018_122733.log'

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
state=torch.load(RUN/'model_0.pt',map_location='cpu',weights_only=False)
contract=state['environment_contract'];assert state['carrybox_schema']==2
assert contract['migration_revision']==13 and contract['amp_shape']==[10,60]
assert contract['reset_probs']==[.8,0.,.2] and contract['held_box_reference_reset']
amp=state['amp'];assert amp['config']['schema']==3 and amp['config']['frame_dim']==60
assert amp['dataset']['clip_count']==13 and amp['statistics_initialized']
assert state['pose_aux_coef']==.1 and amp['config']['ppo']['schedule']=='adaptive'
assert amp['model']['running_count']>0
for model in (state['model_state_dict'],amp['model']):assert all(torch.isfinite(v).all() for v in model.values())
for opt in (state['optimizer_state_dict'],amp['optimizer']):
    assert opt['state']
    for entry in opt['state'].values():
        for value in entry.values():
            if isinstance(value,torch.Tensor):assert torch.isfinite(value).all()
# Ensure completed iterations, not just an alive process or a growing startup log.
time.sleep(12)
end=rows();assert end[-1]['iteration']>start[-1]['iteration']
command=Path(f'/proc/{PID}/cmdline').read_bytes().replace(b'\0',b' ').decode()
assert '--task Template-Perceptual-Ball-CarryBox-Walled5-v0' in command and '--num_envs 4096' in command
warm=end[1:][-10:];assert warm
result=dict(status='PASS',checked_at=datetime.now().astimezone().isoformat(timespec='seconds'),pid=PID,command=command,
    run=str(RUN),log=str(LOG),progress_from=start[-1]['iteration'],progress_to=end[-1]['iteration'],
    recent_iterations=warm,mean_iteration_seconds=sum(x['seconds'] for x in warm)/len(warm),max_iteration_seconds=max(x['seconds'] for x in warm),
    checkpoint=str(RUN/'model_0.pt'),environment_contract=contract,amp_config=amp['config'],amp_dataset=amp['dataset'],
    finite_policy_and_amp=True,finite_nonempty_optimizers=True,normalizer_count=float(amp['model']['running_count']),
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,memory.free,utilization.gpu','--format=csv,noheader'],text=True).strip(),
    convergence='not_evaluated',process_modified=False)
(OUT/'snapshot.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','checked_at','pid','progress_from','progress_to','mean_iteration_seconds','max_iteration_seconds')},ensure_ascii=False))
