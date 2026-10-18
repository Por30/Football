"""Restart authorized formal run only after equivalent full-config benchmark passes."""
from pathlib import Path
from datetime import datetime
import subprocess,json,hashlib,torch
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
ckpt=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-18_12-27-37_wall5_v13_hold_rsi/model_0.pt'
candidate=json.loads((OUT/'candidate.json').read_text());assert candidate['strict_restore'] and candidate['rsi_equivalence']['rng_equal']
warm=[r['collection_time']+r['learn_time'] for r in candidate['iterations'] if 2<=r['it']<=5]
assert sum(warm)/len(warm)<6.,warm
assert not Path('/proc/3804340').exists(),'Old run still alive'
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():continue
    try:cmd=proc.joinpath('cmdline').read_bytes().replace(b'\0',b' ').decode()
    except (FileNotFoundError,PermissionError,ProcessLookupError):continue
    if 'scripts/rsl_rl/train.py' in cmd and '--task Template-Perceptual-Ball' in cmd:
        raise RuntimeError('Another production training process exists: '+proc.name)
state=torch.load(ckpt,map_location='cpu',weights_only=False);iteration=int(state['iter']);assert iteration==0
stamp=datetime.now().strftime('%Y%m%d_%H%M%S');name='wall5_v13_perf_'+stamp
log=ckpt.parent.parent/('launch_'+name+'.log')
cmd=['/home/cao/ENTER/envs/ball/bin/python','-u','scripts/rsl_rl/train.py','--task','Template-Perceptual-Ball-CarryBox-Walled5-v0','--num_envs','4096','--device','cuda:0','--headless','--seed','42','--max_iterations',str(40000-iteration),'--run_name',name,'--resume','--checkpoint',str(ckpt)]
with log.open('w') as stream:
    proc=subprocess.Popen(cmd,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
result=dict(pid=proc.pid,log=str(log),run_name=name,source_checkpoint=str(ckpt),source_sha256=hashlib.sha256(ckpt.read_bytes()).hexdigest(),command=cmd,started_at=datetime.now().astimezone().isoformat(),source_iteration=iteration)
(OUT/'restart.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
