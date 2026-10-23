from pathlib import Path
import json,hashlib,datetime
import numpy as np
D=Path(__file__).resolve().parent;R=D.parents[2];s=json.loads((D/'selection.json').read_text());p=json.loads((D/'probe.json').read_text());log=json.loads((D/'training_analysis.json').read_text())
assert p['status']=='PASS' and p['weights_unchanged']
for path,h in s['sources'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==h,path
assert hashlib.sha256(Path(s['checkpoint']).read_bytes()).hexdigest()==s['checkpoint_sha256']
proc=Path(f"/proc/{s['launch']['pid']}")
cmd=[x.decode() for x in (proc/'cmdline').read_bytes().split(b'\0') if x];assert cmd==s['launch']['command']
assert (proc/'stat').read_text().split(') ',1)[1].split()[19]==s['start_ticks']
error=np.concatenate([b['error'] for b in p['fk']]);parts={'height':(0,1),'joints':(1,30),'ends':(30,45),'linear':(45,48),'angular':(48,51),'rot6':(51,57),'box':(57,60)}
fk={k:dict(mean_abs=float(error[:,a:b].mean()),max_abs=float(error[:,a:b].max())) for k,(a,b) in parts.items()}
summary=dict(status='PASS',checked_at=datetime.datetime.now().astimezone().isoformat(),checkpoint=p['checkpoint'],checkpoint_iteration=p['iteration'],log_iteration=log['iteration'],fk_feature_errors=fk,per_feature_max_abs=error.max(0).tolist(),expert_group=p['expert_group'],expert_padding=p['padding'],replay={mode:{'groups':v['groups'],'age_style':v['age_style']} for mode,v in p['runs'].items()},formal_process_unchanged=True,source_and_checkpoint_unchanged=True)
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
