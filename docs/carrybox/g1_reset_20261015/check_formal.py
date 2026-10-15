"""Read-only receipt for the explicitly authorized background training launch."""
import json,re,datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import torch
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];launch=json.loads((OUT/'launch.json').read_text());pid=launch['pid']
cmd=Path(f'/proc/{pid}/cmdline').read_bytes().decode().split('\0');assert any(a.endswith('/train.py') for a in cmd)
assert '--warm_start_carrybox' not in cmd and '--resume' not in cmd
text=Path(launch['log']).read_text(errors='replace');text=re.sub(r'\x1b\[[0-9;]*m','',text)
iters=[int(x) for x in re.findall(r'Learning iteration\s+(\d+)/',text)];assert iters and max(iters)>=10, f'waiting for iteration10: {iters[-1:]}'
times=[float(x) for x in re.findall(r'Iteration time:\s+([\d.]+)s',text)];assert len(times)>=10
run=next((ROOT/'logs/rsl_rl/g1_carrybox_depth/walled4').glob('*_'+launch['run_name']));model=run/'model_0.pt';state=torch.load(model,map_location='cpu',weights_only=False)
assert state['carrybox_schema']==2;contract=state['environment_contract'];assert contract['migration_revision']==8 and contract['variant']=='walled4'
assert contract['reset_probs']==[.6,.3,.1] and contract['obstacle_cylinders']==3
assert state['amp']['dataset']['clip_count']==15
for values in [state['model_state_dict'],state['amp']['model']]:assert all(torch.isfinite(v).all() for v in values.values())
yaml=(run/'params/env.yaml').read_text();assert re.search(r'num_envs: 4096\b',yaml)
assert not (run/'initialization.json').exists()
report=dict(status='RUNNING_VERIFIED',verified_at=datetime.datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),pid=pid,run=str(run),log=launch['log'],checkpoint=str(model),schema=2,revision=8,dataset=state['amp']['dataset'],checkpoint_parameters_finite=True,initialization='fresh',last_iteration=max(iters),num_envs=4096,initial_std_mean=float(state['model_state_dict']['log_std'].exp().mean()),warm_iteration_seconds=times[2:],warm_mean_seconds=sum(times[2:])/len(times[2:]),warm_max_seconds=max(times[2:]))
assert report['warm_max_seconds']<=6., report
(OUT/'formal_check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='dataset'},indent=2))
