from pathlib import Path
import json,hashlib,math
D=Path(__file__).resolve().parent;ROOT=D.parents[2];s=json.loads((D/'selection.json').read_text())
for name,digest in s['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
for path,key in [('checkpoint','checkpoint_sha256'),('old_checkpoint','old_checkpoint_sha256')]:assert hashlib.sha256(Path(s[path]).read_bytes()).hexdigest()==s[key]
summary={}
for mode in ('on','off'):
 d=json.loads((D/f'{mode}.json').read_text());assert d['status']=='PASS' and d['policy_parameters_unchanged']
 summary[mode]={}
 for name,c in d['cases'].items():
  assert len(c['episodes'])==24 and all(e['skill']==0 and 0<e['steps']<=1000 for e in c['episodes'])
  assert math.isfinite(c['summary']['mean_task_per_step'])
  assert c['summary']['samples']==sum(e['steps'] for e in c['episodes'])
  summary[mode][name]=c['summary']
cmd=Path(f'/proc/{s["training_pid"]}/cmdline')
assert cmd.exists() and [a.decode() for a in cmd.read_bytes().split(b'\0') if a]==s['training_command']
assert Path(f'/proc/{s["training_pid"]}/stat').read_text().split(') ',1)[1].split()[19]==s['training_start_ticks']
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('DIAGNOSIS_CHECK_PASS')
