"""Read-only identity and parameter comparison: recorded rev17 versus live rev28."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import torch
import yaml

D = Path(__file__).resolve().parent
R = D.parents[2]
old_selection = json.loads((R/'docs/carrybox/wall5_latest_play_20261020/selection.json').read_text())
current_selection = json.loads((R/'docs/carrybox/wall5_amp_reward_audit_20261023/selection.json').read_text())
launch = json.loads((R/'docs/carrybox/wall5_clean_camera_20261023/launch.json').read_text())
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
paths = [Path(s['checkpoint']) for s in (old_selection, current_selection)]
for s in (old_selection, current_selection):
    assert sha(s['checkpoint']) == s['checkpoint_sha256']
models = [torch.load(p, map_location='cpu', weights_only=False) for p in paths]
assert [m['environment_contract']['migration_revision'] for m in models] == [17, 28]
assert [m['iter'] for m in models] == [2800, 4800]
assert json.loads(json.dumps(models[0]['environment_contract'])) == old_selection['environment_contract']
for name, digest in launch['source_sha256'].items():
    assert sha(R/name) == digest, name
historical = {}
for name, digest in old_selection['source_sha256'].items():
    raw = subprocess.check_output(['git', 'show', '89b93e1:'+name], cwd=R)
    assert hashlib.sha256(raw).hexdigest() == digest, name
    historical[name] = digest
pid = launch['pid']
assert Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')[:-1] == [x.encode() for x in launch['command']]

def differences(a, b, prefix=''):
    result = {}
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(a.keys() | b.keys()):
            result.update(differences(a.get(k), b.get(k), prefix+'.'+k))
    elif a != b:
        result[prefix.lstrip('.')] = {'old': a, 'current': b}
    return result

envs = [yaml.load((p.parent/'params/env.yaml').read_text(), Loader=yaml.BaseLoader) for p in paths]
agents = [yaml.load((p.parent/'params/agent.yaml').read_text(), Loader=yaml.BaseLoader) for p in paths]
old, new = envs
same = {
    'robot_actuators': old['scene']['robot']['actuators'] == new['scene']['robot']['actuators'],
    'robot_initial_default_state': old['scene']['robot']['init_state'] == new['scene']['robot']['init_state'],
    'physics_dt': old['sim']['dt'] == new['sim']['dt'],
    'decimation': old['decimation'] == new['decimation'],
    'episode_length_s': old['episode_length_s'] == new['episode_length_s'],
    'action_scale': old['actions']['joint_pos']['scale'] == new['actions']['joint_pos']['scale'],
    'torque_reward': old['rewards']['torques'] == new['rewards']['torques'],
    'action_rate_reward': old['rewards']['action_rate'] == new['rewards']['action_rate'],
    'policy_config': agents[0]['policy'] == agents[1]['policy'],
    'amp_ppo_recipe': models[0]['amp']['config']['ppo'] == models[1]['amp']['config']['ppo'],
    'camera_nominal_offset': old['scene']['depth_camera']['offset'] == new['scene']['depth_camera']['offset'],
}
assert all(same.values()), same
assert [m['pose_aux_coef'] for m in models] == [.1, 1.]
assert [m['amp']['dataset']['clip_count'] for m in models] == [13, 15]
result = dict(status='PASS', checked_at=datetime.datetime.now().astimezone().isoformat(),
    checkpoints=[dict(path=str(p), sha256=sha(p), iteration=m['iter'], contract=m['environment_contract'],
                      aux_coef=m['pose_aux_coef'], amp=m['amp']['config'], dataset=m['amp']['dataset'])
                 for p, m in zip(paths, models)],
    old_git_revision='89b93e1', old_verified_sources=historical,
    current_source_sha256=launch['source_sha256'], training_pid=pid, production_unchanged=True,
    same=same, contract_diff=differences(models[0]['environment_contract'], models[1]['environment_contract']),
    environment_diff=differences(*envs), agent_diff=differences(*agents))
(D/'comparison.json').write_text(json.dumps(result, indent=2)+'\n')
print('COMPARISON_PASS', json.dumps(same))
