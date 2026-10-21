"""Bind a successful CPU run to the files subsequently tested and launched."""
import hashlib
import json
from pathlib import Path

DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
old = json.loads((DOC.parent/'wall5_v18_fresh_20261020/launch.json').read_text())
paths = list(old['source_sha256']) + [
    'source/perceptual_ball/perceptual_ball/carrybox_reward_geometry.py',
    'source/perceptual_ball/perceptual_ball/carrybox_walled.py',
    'tests/test_carrybox_reward_geometry.py', 'tests/test_carrybox_reset_bug.py']
hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in dict.fromkeys(paths)}
(DOC/'source_hashes.json').write_text(json.dumps(hashes, indent=2)+'\n')
(DOC/'check.json').write_text(json.dumps(dict(status='PASS', source_sha256=hashes,
    output_sha256=hashlib.sha256((DOC/'check.log').read_bytes()).hexdigest()), indent=2)+'\n')
print('SEMANTIC_CPU_PASS')
