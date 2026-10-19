"""One authorized switch to a fresh 4096-env Wall5 run, after CPU/simulator checks."""
from pathlib import Path
from datetime import datetime
import json,os,signal,subprocess,time,hashlib
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2]
for kind in ('cpu','smoke'):
    tests=json.loads((DOC/f'receipts_{kind}.json').read_text())['tests']
    assert tests and all(t['result']=='PASS' and t['executed'] for t in tests)
assert not (DOC/'launch.json').exists(),'Already launched; inspect instead of restarting again'
old=json.loads((ROOT/'docs/carrybox/wall5_fresh_20261018/launch.json').read_text())
pid=old['pid'];proc=Path(f'/proc/{pid}');cmd=proc.joinpath('cmdline').read_bytes().split(b'\0')
actual=[x.decode() for x in cmd if x];assert actual==old['command'],actual
assert '--num_envs' in actual and actual[actual.index('--num_envs')+1]=='4096'
old['stopping_at']=datetime.now().astimezone().isoformat();old['signal']='SIGINT';old['proc_start_ticks']=proc.joinpath('stat').read_text().split()[21]
(DOC/'stopped_run.json').write_text(json.dumps(old,indent=2)+'\n')
os.kill(pid,signal.SIGINT)
for _ in range(45):
    if not proc.exists() or proc.joinpath('stat').read_text().split()[2]=='Z':break
    time.sleep(1)
else:raise RuntimeError('Target process did not exit after SIGINT; no replacement launched')
old['stopped_at']=datetime.now().astimezone().isoformat()
old_runs=list((ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5').glob('*_'+old['run_name']));assert len(old_runs)==1
models=sorted(old_runs[0].glob('model_*.pt'),key=lambda p:int(p.stem.split('_')[-1]));assert models
old['last_checkpoint']=str(models[-1]);old['last_checkpoint_sha256']=hashlib.sha256(models[-1].read_bytes()).hexdigest()
(DOC/'stopped_run.json').write_text(json.dumps(old,indent=2)+'\n')
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():continue
    try:args=proc.joinpath('cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError,PermissionError,ProcessLookupError):continue
    if b'scripts/rsl_rl/train.py' in args and b'--task' in args:raise RuntimeError('Another training process exists: '+proc.name)
free=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits','-i','0'],text=True).strip())
assert free>18000,free
stamp=datetime.now().strftime('%Y%m%d_%H%M%S');name='wall5_v14_asymmetric_fresh_'+stamp
log=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5'/('launch_'+name+'.log')
command=['/home/cao/ENTER/envs/ball/bin/python','-u','scripts/rsl_rl/train.py','--task','Template-Perceptual-Ball-CarryBox-Walled5-v0','--num_envs','4096','--device','cuda:0','--headless','--seed','42','--max_iterations','40000','--run_name',name]
with log.open('x') as stream:
    p=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
record=dict(pid=p.pid,log=str(log),command=command,run_name=name,initialization='fresh',started_at=datetime.now().astimezone().isoformat())
(DOC/'launch.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
