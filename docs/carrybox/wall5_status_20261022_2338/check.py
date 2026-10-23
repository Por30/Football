from pathlib import Path
import json, hashlib, datetime, re, math, statistics
import torch

D = Path(__file__).resolve().parent
R = D.parents[2]
s = json.loads((D/'selection.json').read_text())
pid = s['launch']['pid']
assert [x.decode() for x in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if x] == s['launch']['command']
assert Path(f'/proc/{pid}/stat').read_text().split()[21] == s['pid_start_ticks']
for name, digest in s['launch']['source_sha256'].items():
    assert hashlib.sha256((R/name).read_bytes()).hexdigest() == digest, name
parser = R/'docs/carrybox/wall5_training_audit_20261022/analyze.py'
exec(compile(parser.read_text(), str(parser), 'exec'), {'__file__':str(D/'check.py')})
a = json.loads((D/'training_analysis.json').read_text())
rows = json.loads((D/'curve.json').read_text())
assert a['iteration'] > 1255
assert all(math.isfinite(v) for row in rows for v in row.values())
raw = (D/'training_snapshot.log').read_text()
errors = [line for line in raw.splitlines() if re.search(
    r'Traceback \(most recent call last\)|CUDA out of memory|illegal memory access|FloatingPointError|:\s*[-+]?(?:nan|inf)\s*$', line, re.I)]
assert not errors, errors[-5:]
torch.set_num_threads(2)
ck = torch.load(s['checkpoint'], map_location='cpu', weights_only=False)
assert int(ck['iter']) == 1200
counts = {}
for key, tensors in [('policy',ck['model_state_dict']), ('amp',ck['amp']['model'])]:
    assert all(torch.isfinite(v).all() for v in tensors.values() if torch.is_tensor(v))
    counts[key] = sum(v.numel() for v in tensors.values() if torch.is_tensor(v))
assert hashlib.sha256(Path(s['checkpoint']).read_bytes()).hexdigest() == s['checkpoint_sha256']
last100 = rows[-100:]
means = {k:statistics.mean(row[k] for row in last100) for k in last100[0]}
previous = json.loads((R/'docs/carrybox/wall5_training_audit_20261022/training_analysis.json').read_text())
out = dict(status='PASS',checked_at=datetime.datetime.now().astimezone().isoformat(),pid=pid,
    iteration=a['iteration'],checkpoint=s['checkpoint'],checkpoint_iter=1200,
    model_finite_elements=counts,log_errors=errors,source_unchanged=True,
    latest100=means,recent_completed_estimates=a['recent_completed_estimates'],
    prior_iteration=previous['iteration'],prior_recent_completed=previous['recent_completed_estimates'],
    maximum_iteration_seconds_last100=max(r['Iteration time'] for r in last100),
    log_mtime=datetime.datetime.fromtimestamp(Path(s['launch']['log']).stat().st_mtime).astimezone().isoformat())
(D/'health.json').write_text(json.dumps(out,indent=2)+'\n')
print('HEALTH_CHECK_PASS',json.dumps(out,ensure_ascii=False))
