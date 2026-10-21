"""Read-only evidence for the supplied rev18/X2 comparison; no simulator updates."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import math
import re
import statistics
import torch

torch.set_num_threads(1)
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
attachment = Path('/home/cao/.codex/attachments/6dbd0199-765e-4ca9-90d1-c1e5444854b2/pasted-text.txt')
launch = json.loads((OUT.parent / 'wall5_v18_fresh_20261020/launch.json').read_text())
proc = Path(f'/proc/{launch["pid"]}/cmdline')
command = [v.decode() for v in proc.read_bytes().split(b'\0') if v]
assert command == launch['command']
for path, expected in launch['source_sha256'].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
run = next((ROOT / 'logs/rsl_rl/g1_carrybox_depth/walled5').glob('*_' + launch['run_name']))
model = torch.load(run / 'model_0.pt', map_location='cpu', weights_only=False)
c = model['environment_contract']
assert c['migration_revision'] == 18 and c['task_box_distance']['metric'] == 'xyz_l2'
assert c['task_box_distance']['threshold_m'] == .7
assert c['reward_weights']['locomotion_stability'] == 5.
assert c['reward_weights']['walk_task'] == 1.
assert c['early_failure_penalty_weight'] == -50.

# Equivalent horizontal radius for the heights supplied in the attachment.
x2_pelvis, g1_pelvis, box = .669, .775, .125
x2_radius = math.sqrt(.7**2 - (x2_pelvis-box)**2)
g1_radius = math.sqrt(.7**2 - (g1_pelvis-box)**2)
equivalent = math.sqrt(x2_radius**2 + (g1_pelvis-box)**2)
assert .78 < equivalent < .79
geometry = dict(source='Heights supplied in attachment, not new simulator calibration',
                x2_pelvis_m=x2_pelvis, g1_pelvis_m=g1_pelvis, box_center_m=box,
                x2_xy_radius_m=x2_radius, g1_xy_radius_m=g1_radius,
                g1_equivalent_xyz_gate_m=equivalent)

# Existing physical measurements: historical reset snapshots, not settled rev18 stand calibration.
old_path = ROOT / 'docs/carrybox/g1_reset_20261015/probe.json'
old = json.loads(old_path.read_text())
heads = {}
for name in ('default_stand', 'hold_rsi_loco'):
    rows = old[name]['initial']
    heads[name] = {k: dict(n=len(rows), mean=statistics.mean(r[k] for r in rows),
                          min=min(r[k] for r in rows), max=max(r[k] for r in rows))
                   for k in ('root_z', 'head_z')}

log_path = Path(launch['log'])
with log_path.open('rb') as f:
    f.seek(max(0, log_path.stat().st_size-500000))
    log = f.read().decode(errors='replace')
log = re.sub(r'\x1b\[[0-9;]*m', '', log)
blocks = re.split(r'Learning iteration (\d+)/40000', log)
complete = [(int(blocks[i]), blocks[i+1]) for i in range(1, len(blocks)-1, 2)
            if re.search(r'Iteration time:\s*[\d.]+s', blocks[i+1])]
assert complete
iteration, latest = complete[-1]
keys = ['Mean episode length', 'Episode_Termination/time_out', 'Skill/loco_mean_steps',
        'Skill/loco_success_fraction', 'Reward/loco_locomotion_stability_per_step',
        'Reward/loco_walk_task_per_step', 'Reward/loco_task_per_step',
        'Motion/loco_survivor_speed_mps', 'Motion/loco_survivor_box_distance_xy_m',
        'Motion/loco_survivor_box_distance_m', 'Reward/task_weighted_per_step',
        'Reward/amp_per_step', 'AMP/style_reward', 'Iteration time']
metrics = {}
for key in keys:
    found = re.findall(re.escape(key) + r':\s*([-+\d.eE]+)', latest)
    if found:
        metrics[key] = float(found[-1])
assert metrics['Reward/loco_walk_task_per_step'] > 0
ratio = metrics['Reward/loco_locomotion_stability_per_step'] / metrics['Reward/loco_walk_task_per_step']
result = dict(
    status='PASS', checked_at=datetime.now().astimezone().isoformat(),
    attachment=str(attachment), attachment_sha256=hashlib.sha256(attachment.read_bytes()).hexdigest(),
    source_sha256=launch['source_sha256'], current_run=str(run), pid=launch['pid'],
    sampled_complete_iteration=iteration, current_metrics=metrics,
    stability_to_walk_raw_step_reward_ratio=ratio,
    theoretical_max_raw_per_step=dict(stability=5*.02, walk=1.5*.02, carryup=3.7*.02),
    theoretical_max_after_task_mix=dict(stability=.75*5*.02, walk=.75*1.5*.02,
                                        carryup=.75*3.7*.02),
    geometry=geometry,
    historical_head_source=str(old_path.relative_to(ROOT)),
    historical_head_source_sha256=hashlib.sha256(old_path.read_bytes()).hexdigest(),
    historical_reset_head_heights=heads,
    limits=['X2 source and training params not independently available here',
            'No new G1 settled-height or foot-clearance measurement',
            'Reward magnitudes and a single trajectory do not establish causal failure',
            'Skill/loco_mean_steps is cumulative; Mean episode length is a different logging statistic'],
    production_changed=False, training_stopped_or_restarted=False,
)
(OUT / 'evidence.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
print(json.dumps(result, indent=2, ensure_ascii=False))
