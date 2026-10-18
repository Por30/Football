from pathlib import Path
from datetime import datetime
import json,subprocess,time
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
for _ in range(30):
    if not Path('/proc/3810947').exists():break
    time.sleep(1)
else:raise RuntimeError('Previous wall5 has not exited')
processes=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader'],text=True)
for line in processes.splitlines():
    if int(line.split(',')[1].split()[0])>1024:raise RuntimeError('GPU still busy: '+line)
stamp=datetime.now().strftime('%Y%m%d_%H%M%S');name='wall5_v13_perf_fresh_'+stamp
log=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5'/('launch_'+name+'.log')
cmd=['/home/cao/ENTER/envs/ball/bin/python','-u','scripts/rsl_rl/train.py','--task','Template-Perceptual-Ball-CarryBox-Walled5-v0','--num_envs','4096','--device','cuda:0','--headless','--seed','42','--max_iterations','40000','--run_name',name]
assert not any('--resume' in a or '--checkpoint' in a or '--warm_start' in a for a in cmd)
with log.open('w') as stream:
    p=subprocess.Popen(cmd,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
result=dict(pid=p.pid,log=str(log),run_name=name,command=cmd,initialization='fresh',started_at=datetime.now().astimezone().isoformat())
(OUT/'launch.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
