from pathlib import Path
import hashlib,json,sys
D=Path(__file__).resolve().parent;R=D.parents[2]
paths=list((R/'source/perceptual_ball/perceptual_ball').rglob('*.py'))
paths+=list((R/'source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof').rglob('*.usd'))
paths+=[R/'tests/test_carrybox_physhsi.py']
h={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
p=D/'validated_sources.json'
if '--record' in sys.argv:
 if p.exists():
  assert json.loads(p.read_text())['source_sha256']==h,'Sources changed; preserve failed receipt before re-record'
 else:p.write_text(json.dumps({'source_sha256':h},indent=2)+'\n')
else:assert json.loads(p.read_text())['source_sha256']==h
print('SOURCE_IDENTITY_OK',len(h))
