from pathlib import Path
import hashlib, json, sys
DOC=Path(__file__).resolve().parent
ROOT=DOC.parents[2]
before=json.loads((DOC/'before.json').read_text())
paths=sorted(set(before['old_launch']['source_sha256']) | set(before['source_before']) | {'tests/test_carrybox_depth_metres.py'})
hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
path=DOC/'validated_sources.json'
if '--record' in sys.argv:
    assert not path.exists()
    path.write_text(json.dumps(dict(source_sha256=hashes),indent=2)+'\n')
else:
    assert json.loads(path.read_text())['source_sha256']==hashes, 'Source changed after validation snapshot'
print('SOURCE_IDENTITY_OK', len(hashes))
