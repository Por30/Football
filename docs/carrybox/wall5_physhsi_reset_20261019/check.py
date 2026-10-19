"""CPU-only provenance and reset-data audit; never imports either simulator."""
import ast
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

import torch

torch.set_num_threads(1)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PHY = Path('/home/cao/PhysHSI/legged_gym')
hashes = json.loads((HERE / 'source_hashes.json').read_text())
for name, expected in hashes.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name


def assignment(path, names):
    node = ast.parse(path.read_text())
    for name in names[:-1]:
        node = next(n for n in node.body if isinstance(n, ast.ClassDef) and n.name == name)
    statement = next(n for n in node.body if isinstance(n, (ast.Assign, ast.AnnAssign))
                     and any(isinstance(t, ast.Name) and t.id == names[-1]
                             for t in (n.targets if isinstance(n, ast.Assign) else [n.target])))
    return ast.literal_eval(statement.value)


cfg = PHY / 'legged_gym/envs/g1/carrybox_config.py'
hybrid = assignment(cfg, ['G1Cfg', 'asset', 'box', 'hybrid_init_prob'])
weights = assignment(cfg, ['G1Cfg', 'asset', 'box', 'skill_init_prob'])
skills = assignment(cfg, ['G1Cfg', 'asset', 'box', 'skill'])
fractions = {'default': 1 - hybrid, **{k: hybrid * v / sum(weights) for k, v in zip(skills, weights)}}
assert abs(sum(fractions.values()) - 1) < 1e-10

dataset = ROOT / 'source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup'
manifest = json.loads((dataset / 'amp_manifest.json').read_text())
rows, speed_values, sample_weights = [], [], []
loco = [x for x in manifest['clips'] if x['group'] == 'loco_direction']
for item in manifest['clips']:
    path = dataset / item['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], str(path)
    if item['group'] != 'loco_direction':
        continue
    data = torch.load(path, map_location='cpu', weights_only=True)
    velocity = data['base_position'].double().diff(dim=0) * manifest['fps']
    assert torch.isfinite(velocity).all()
    speed = velocity[:, :2].norm(dim=-1)
    old_path = PHY / 'resources/dataset/dataset_carrybox' / item['source_file']
    rows.append(dict(file=item['file'], reset_frames=len(speed), mean_speed_xy_mps=speed.mean().item(),
                     max_speed_xy_mps=speed.max().item(),
                     physhsi_source_equal=hashlib.sha256(old_path.read_bytes()).hexdigest() == item['sha256']))
    speed_values.append(speed)
    sample_weights.append(torch.full_like(speed, 1 / (len(loco) * len(speed))))
speed, weights_t = torch.cat(speed_values), torch.cat(sample_weights)
ordered, indices = speed.sort()
cdf = weights_t[indices].cumsum(0)
quantiles = {str(q): ordered[torch.searchsorted(cdf, q)].item() for q in (.5, .9, .95, .99)}
stats = dict(sampling='uniform over clips; uniform native frames 0..N-2 inside each clip',
             num_clips=len(loco), num_candidate_frames=len(speed),
             mean_mps=(speed * weights_t).sum().item(), quantiles_mps=quantiles,
             max_mps=speed.max().item(),
             fraction_above_physhsi_rsi_xy_max=(weights_t * (speed > 2**.5 * .2)).sum().item(),
             physhsi_rsi_xy_max_mps=2**.5 * .2,
             physhsi_rsi_xy_rms_mps=(2 * .2**2 / 3)**.5)

launch = json.loads((ROOT / 'docs/carrybox/wall5_reset_bug_20261019/launch.json').read_text())
pid = launch['pid']
proc = Path(f'/proc/{pid}/cmdline')
cmd = proc.read_bytes().replace(b'\0', b' ').decode() if proc.exists() else None
log = Path(launch['log'])
log_text = re.sub(r'\x1b\[[0-9;]*m', '', log.read_text(errors='replace'))
iterations = re.findall(r'Learning iteration\s+(\d+)\s*/', log_text)
times = [float(x) for x in re.findall(r'Iteration time:\s+([\d.]+)s', log_text)]
snapshot = dict(checked_at=datetime.now().astimezone().isoformat(), pid=pid, cmd=cmd,
                latest_iteration=int(iterations[-1]) if iterations else None,
                recent_10_iteration_seconds=times[-10:])
for name, expected in hashes.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
result = dict(status='PASS', scope='CPU static/data audit only; no physical rollouts',
              source_hashes=hashes, physhsi_reset_fractions=fractions,
              wall5_loco_root_speed=stats, clips=rows, training_snapshot=snapshot)
(HERE / 'evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('source_hashes', 'clips')}, ensure_ascii=False, indent=2))
