"""CPU-only effective-config, call-path and source-identity audit."""
from pathlib import Path
import ast, datetime, hashlib, json, os, subprocess, sys
import numpy as np
import yaml

D = Path(__file__).resolve().parent
R = D.parents[2]
P = Path('/home/cao/PhysHSI')
S = R/'source/perceptual_ball/perceptual_ball'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
source = [P/p for p in (
    'README.md', 'legged_gym/legged_gym/envs/__init__.py',
    'legged_gym/legged_gym/envs/base/legged_robot_config.py',
    'legged_gym/legged_gym/envs/g1/carrybox.py',
    'legged_gym/legged_gym/envs/g1/carrybox_config.py',
    'legged_gym/legged_gym/envs/g1/carrybox_resume_config.py',
    'legged_gym/legged_gym/envs/motionlib/motionlib_carrybox.py',
    'legged_gym/legged_gym/scripts/play.py',
    'legged_gym/resources/config/carrybox.yaml', 'legged_gym/resources/config/joint_id.txt',
    'legged_gym/resources/robots/g1/urdf/g1_29dof.urdf',
    'rsl_rl/rsl_rl/algorithms/him_ppo.py', 'rsl_rl/rsl_rl/modules/amp.py',
    'rsl_rl/rsl_rl/modules/actor_critic.py', 'rsl_rl/rsl_rl/runners/him_on_policy_runner.py',
    'rsl_rl/rsl_rl/storage/him_rollout_storage.py')]
source += [S/p for p in (
    'carrybox_amp.py', 'carrybox_wall5.py', 'carrybox_wall10.py', 'carrybox_physhsi.py',
    'carrybox_reward_geometry.py', 'carrybox_walled.py', 'carrybox_warp_camera.py', 'carrybox_raycast.py',
    'assets/robots/g1_29dof.py', 'assets/robots/g1_29dof/config.yaml',
    'rsl_rl_extensions/carrybox.py', 'rsl_rl_extensions/carrybox_wall5.py',
    'rsl_rl_extensions/carrybox_wall10.py', 'rsl_rl_extensions/amp.py', 'rsl_rl_extensions/modules.py',
    'tasks/manager_based/perceptual_ball/__init__.py',
    'tasks/manager_based/perceptual_ball/carrybox_env_cfg.py',
    'tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py',
    'tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py',
    'tasks/manager_based/perceptual_ball/carrybox_wall10_env_cfg.py',
    'tasks/manager_based/perceptual_ball/mdp/carrybox.py',
    'tasks/manager_based/perceptual_ball/mdp/carrybox_state.py',
    'tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py',
    'tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py',
    'tasks/manager_based/perceptual_ball/mdp/carrybox_wall10.py',
    'tasks/manager_based/perceptual_ball/mdp/carrybox_physhsi.py',
    'tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py')]
source += list((S/'assets/robots/g1_29dof').rglob('*.usd'))
snapshot = {str(p): sha(p) for p in source}
freeze = D/'source_identity.json'
if freeze.exists():
    assert snapshot == json.loads(freeze.read_text()), 'Sources changed during audit'
else:
    freeze.write_text(json.dumps(snapshot, indent=2)+'\n')

# Evaluate only local config class definitions with a trivial BaseConfig, no Gym/Sim imports.
ns = {'BaseConfig': type('BaseConfig', (), {}), 'np': np}
def config(path):
    tree = ast.parse(path.read_text())
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    exec(compile(ast.Module(body=classes, type_ignores=[]), str(path), 'exec'), ns)
def plain(cls):
    result = {}
    for key in dir(cls):
        if key.startswith('_'): continue
        value = getattr(cls, key)
        if isinstance(value, type): result[key] = plain(value)
        elif not callable(value): result[key] = value
    return result
config(P/'legged_gym/legged_gym/envs/base/legged_robot_config.py')
config(P/'legged_gym/legged_gym/envs/g1/carrybox_config.py')
base = dict(env=plain(ns['G1Cfg']), agent=plain(ns['G1CfgPPO']))
config(P/'legged_gym/legged_gym/envs/g1/carrybox_resume_config.py')
resume = dict(env=plain(ns['G1Cfg']), agent=plain(ns['G1CfgPPO']))
assert base['env']['env']['num_actor_obs'] == 738
assert base['env']['env']['num_privileged_obs'] == 126
assert base['agent']['runner']['num_steps_per_env'] == 100
assert not base['env']['amp']['use_normalizer']
assert base['env']['amp']['amp_coef'] == .25 and resume['env']['amp']['amp_coef'] == .3
run = R/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-23_17-35-18_wall5_v28_clean_camera_fresh_20261023_173513'
current = {k: yaml.load((run/'params'/f'{k}.yaml').read_text(), Loader=yaml.BaseLoader) for k in ('env', 'agent')}
assert current['agent']['num_steps_per_env'] == '24'
assert current['agent']['algorithm']['pose_aux_coef'] == '1.0'
assert current['env']['scene']['box']['spawn']['size'] == ['0.3', '0.3', '0.25']
symbols = {}
for p in source:
    if p.suffix == '.py':
        symbols[str(p)] = {n.name: n.lineno for n in ast.walk(ast.parse(p.read_text()))
                           if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
usd_lib = '/home/cao/isaacsim/extscache/omni.usd.libs-1.0.1+d02c707b.lx64.r.cp310'
env = dict(os.environ, LD_LIBRARY_PATH=usd_lib+'/bin:'+os.environ.get('LD_LIBRARY_PATH',''))
completed = subprocess.run([sys.executable, str(D/'inspect_usd.py')], cwd=R, env=env,
                           text=True, capture_output=True, check=True)
usd = json.loads(completed.stdout)
wall10_validation = json.loads((R/'docs/carrybox/wall10_20261023/receipts.json').read_text())
assert all(x['result'] == 'PASS' for x in wall10_validation['tests'])
result = dict(status='PASS', checked_at=datetime.datetime.now().astimezone().isoformat(),
              source_default=base, source_resume=resume, current_run=str(run), wall5=current,
              source_symbols=symbols, usd=usd, wall10_prior_receipts=wall10_validation,
              scope='CPU source/data audit, no new physics or training run')
(D/'sources.json').write_text(json.dumps(result, indent=2, default=lambda x: x.item())+'\n')
assert snapshot == {str(p): sha(p) for p in source}
print('SOURCE_AUDIT_PASS',len(source),'files; source actor738/critic126; wall5 rollout24')
