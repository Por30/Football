import hashlib
import json
from pathlib import Path

DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
check = json.loads((DOC/'check.json').read_text())
assert check['status'] == 'PASS'
assert hashlib.sha256((DOC/'check.log').read_bytes()).hexdigest() == check['output_sha256']
for name, expected in check['source_sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
