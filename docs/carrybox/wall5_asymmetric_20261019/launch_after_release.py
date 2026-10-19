"""Continue the authorized switch after the stopped process's GPU memory was released."""
from pathlib import Path
from datetime import datetime
import json,subprocess
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2]
old=json.loads((DOC/'stopped_run.json').read_text())
assert old.get('stopped_at') and not Path(f'/proc/{old["pid"]}').exists()
assert not (DOC/'launch.json').exists(),'Do not launch twice'
for kind in ('cpu','smoke'):
    assert all(t['result']=='PASS' for t in json.loads((DOC/f'receipts_{kind}.json').read_text())['tests'])
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():continue
    try:args=proc.joinpath('cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError,PermissionError,ProcessLookupError):continue
    if b'scripts/rsl_rl/train.py' in args and b'--task' in args:raise RuntimeError('Another training process exists: '+proc.name)
free=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits','-i','0'],text=True).strip())
assert free>18000,free
(DOC/'gpu_release.json').write_text(json.dumps(dict(checked_at=datetime.now().astimezone().isoformat(),free_mib=free,
    initial_preflight_free_mib=9366,initial_preflight_launched=False,reason='GPU release lagged process exit; independently rechecked after cleanup'),indent=2))
name='wall5_v14_asymmetric_fresh_'+datetime.now().strftime('%Y%m%d_%H%M%S')
log=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5'/('launch_'+name+'.log')
command=['/home/cao/ENTER/envs/ball/bin/python','-u','scripts/rsl_rl/train.py','--task','Template-Perceptual-Ball-CarryBox-Walled5-v0','--num_envs','4096','--device','cuda:0','--headless','--seed','42','--max_iterations','40000','--run_name',name]
with log.open('x') as stream:
    p=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
record=dict(pid=p.pid,log=str(log),command=command,run_name=name,initialization='fresh',started_at=datetime.now().astimezone().isoformat())
(DOC/'launch.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
