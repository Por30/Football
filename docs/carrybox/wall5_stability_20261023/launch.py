"""Launch one fresh formal wall5 run with the validated PhysHSI hybrid RSI."""
from datetime import datetime
from pathlib import Path
import hashlib, importlib.util, json, shutil, subprocess, time

DOC=Path(__file__).resolve().parent
ROOT=DOC.parents[2]
assert not (DOC/'launch.json').exists(), 'Launch already recorded; verify instead'
assert importlib.util.find_spec('isaacsim') is not None
assert json.loads((DOC/'stopped_run.json').read_text())['status']=='exited'
assert json.loads((DOC/'smoke.json').read_text())['status']=='PASS'
assert (DOC/'smoke_pass').exists()
before=json.loads((DOC/'validated_sources.json').read_text())
for name,digest in before['source_sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():
        continue
    try:
        args=proc.joinpath('cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError,PermissionError,ProcessLookupError):
        continue
    assert not (b'Template-Perceptual-Ball-CarryBox-Walled5-v0' in args and any(a.endswith((b'scripts/rsl_rl/train.py',b'scripts/rsl_rl/play.py')) for a in args)),proc.name
for _ in range(55):
    free=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits','-i','0'],text=True).strip())
    if free>19000:
        break
    time.sleep(1)
assert free>19000,free
assert shutil.disk_usage(ROOT).free>30*1024**3
dataset=ROOT/'source/perceptual_ball/perceptual_ball/assets/motions/findbox'
raw=(dataset/'amp_manifest.json').read_bytes();manifest=json.loads(raw)
assert len(manifest['clips'])==15
for clip in manifest['clips']:
    assert hashlib.sha256((dataset/clip['file']).read_bytes()).hexdigest()==clip['sha256'],clip['file']
name='wall5_v27_stability_fresh_'+datetime.now().strftime('%Y%m%d_%H%M%S')
log=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5'/('launch_'+name+'.log')
command=['/home/cao/ENTER/envs/ball/bin/python','-u','scripts/rsl_rl/train.py',
    '--task','Template-Perceptual-Ball-CarryBox-Walled5-v0','--num_envs','4096',
    '--device','cuda:0','--headless','--seed','42','--max_iterations','40000','--run_name',name]
with log.open('x') as stream:
    proc=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stream,
                          stderr=subprocess.STDOUT,start_new_session=True)
record=dict(pid=proc.pid,command=command,log=str(log),run_name=name,initialization='fresh',
    loaded_checkpoint=None,started_at=datetime.now().astimezone().isoformat(),free_mib_before=free,
    source_sha256=before['source_sha256'],dataset=str(dataset),manifest_sha256=hashlib.sha256(raw).hexdigest(),
    rsi=[2/3,1/6,1/6],hybrid_reference_probability=.8,reset_assignment='fixed_four_way_quota',source_counts=[819,2185,546,546],self_collisions=True,reference_dataset=str(dataset),reference_manifest_sha256=hashlib.sha256(raw).hexdigest(),user_authorization='User requested diagnosing empty-hand immediate falls, fixing confirmed training faults and restarting fresh4096 after validation')
(DOC/'launch.json').write_text(json.dumps(record,indent=2)+'\n')
print('FORMAL_STARTED',json.dumps({k:record[k] for k in ('pid','command','log','initialization','rsi')}),flush=True)
