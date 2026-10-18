"""Read-only CPU extraction; does not import the simulator or alter training."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import statistics
import subprocess

import torch

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
RUN = ROOT / 'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-16_13-45-09_wall5_amp_stage_a'
LOG = RUN.parent / 'launch_20261016_134504.log'
CKPT = RUN / 'model_20600.pt'
DATA = ROOT / 'source/perceptual_ball/perceptual_ball/assets/motions/findbox'
torch.set_num_threads(2)

raw = LOG.read_bytes()
parts = re.split(r'Learning iteration\s+(\d+)/\d+', re.sub(r'\x1b\[[0-9;]*m', '', raw.decode(errors='replace')))
rows = []
for i in range(1, len(parts), 2):
    if 'Iteration time:' not in parts[i + 1]:
        continue
    row = {'iteration': int(parts[i])}
    for line in parts[i + 1].splitlines():
        match = re.match(r'\s*([^:]+):\s*(-?\d+(?:\.\d+)?)(?:s)?\s*$', line)
        if match:
            row[match[1].strip()] = float(match[2])
    rows.append(row)
assert len(rows) >= 100
window = rows[-100:]
means = {k: statistics.mean(r[k] for r in window) for k in window[-1] if all(k in r for r in window)}
means['amp_fraction_of_net_mixed_reward'] = means['Reward/amp_per_step'] / means['Reward/mixed_per_step']
checkpoint = torch.load(CKPT, map_location='cpu', weights_only=False)
assert checkpoint['carrybox_schema'] == 2
assert checkpoint['environment_contract']['migration_revision'] == 9
assert all(torch.isfinite(v).all() for v in checkpoint['model_state_dict'].values())

manifest = json.loads((DATA / 'amp_manifest.json').read_text())
references = []
for clip in manifest['clips']:
    if clip['group'] != 'pickUp':
        continue
    path = DATA / clip['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == clip['sha256']
    data = torch.load(path, map_location='cpu', weights_only=True)
    height = data['base_height'].float().flatten() + .05 + data['box_pos_local'][:, 2].float()
    contact = int(data['contact_index'])
    # Same scalar support estimate as initialize_reference, BEFORE foot correction
    # and the sampled-frame upper bound used by reset_scene.
    support = max(float(height[contact]) - .125, 0.)
    references.append(dict(file=clip['file'], frames=len(height), contact_index=contact,
        box_center_z_before_foot_correction_min=float(height.min()),
        box_center_z_before_foot_correction_max=float(height.max()),
        contact_box_center_z_before_foot_correction=float(height[contact]),
        support_top_before_foot_correction_and_frame_clamp=support,
        box_center_z_first_frame=float(height[0]),
        sampled_frames_before_contact_fraction=contact/(len(height)-1)))

processes = subprocess.check_output(['ps', '-eo', 'pid,lstart,args'], text=True)
processes = [line for line in processes.splitlines()
             if re.search(r'python\S* scripts/rsl_rl/(train|play)\.py', line)]
source_files = ['tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py',
                'tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py',
                'tasks/manager_based/perceptual_ball/mdp/carrybox.py',
                'tasks/manager_based/perceptual_ball/mdp/carrybox_state.py',
                'tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py',
                'tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py',
                'tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py']
hashes = {p: hashlib.sha256((ROOT/'source/perceptual_ball/perceptual_ball'/p).read_bytes()).hexdigest()
          for p in source_files}
result = dict(checked_at=datetime.datetime.now().astimezone().isoformat(),
    log=str(LOG), log_sha256=hashlib.sha256(raw).hexdigest(),
    last_iteration=rows[-1]['iteration'], latest=rows[-1],
    last100_iteration_range=[window[0]['iteration'], window[-1]['iteration']], last100_means=means,
    checkpoint=str(CKPT), checkpoint_sha256=hashlib.sha256(CKPT.read_bytes()).hexdigest(),
    checkpoint_environment_contract=checkpoint['environment_contract'],
    ppo_lr=[g['lr'] for g in checkpoint['optimizer_state_dict']['param_groups']],
    pose_aux_coef=checkpoint['pose_aux_coef'], pickup_reference_geometry=references,
    active_train_play_processes=processes, source_sha256=hashes,
    caveats=['Skill counts are cumulative rollout-averaged log snapshots, not exact raw event counts.',
             'AMP fraction is net reward magnitude, not gradient contribution.',
             'Reference heights precede live foot correction and per-frame support clamp.',
             'No new simulator rollout or contact feasibility test performed.'])
(OUT/'snapshot.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(dict(last_iteration=result['last_iteration'],
    last100_episode_steps=means['Mean episode length'],
    amp_fraction=means['amp_fraction_of_net_mixed_reward'],
    pickup_reference_geometry=references, ppo_lr=result['ppo_lr']), indent=2))
