"""Actual simulation checks for shared wall recipe and obstacle-only variation."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--variant',type=int,required=True);AppLauncher.add_app_launcher_args(p);args=p.parse_args();args.num_envs=4;app=AppLauncher(args).app
import ast,copy,json
from pathlib import Path
import torch,gymnasium as gym
from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import quat_apply
from perceptual_ball.tasks.manager_based.perceptual_ball import carrybox_walled_env_cfg as config
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_env_cfg import CarryBoxPPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task,carrybox as base_task
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy
from perceptual_ball.carrybox_amp import joint_mapping
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent/f'wall{args.variant}';OUT.mkdir(exist_ok=True)
# Reuse established collision/depth audit, replacing only the obstacle list and shared search expectation.
source=(ROOT/'scripts/rsl_rl/smoke_carrybox_walled.py').read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='geometry')
source=ast.get_source_segment(source,node).replace("cfg.search_prob = 1. if args.variant == 4 else 0.","cfg.search_prob = 1.").replace('if args.variant == 4:', 'if True:')
source=source.replace("[(f'cylinder{i}', 2.2, 3.2) for i in range(3)]","[(f'cylinder{i}', 2.2, 3.2) for i in range(cfg.obstacle_cylinder_count)]")
source=source.replace("['platform', 'wall', 'cylinder0', 'cylinder1', 'cylinder2']","['platform', 'wall'] + [f'cylinder{i}' for i in range(cfg.obstacle_cylinder_count)]")
source=source.replace("[('wall', 1.5), ('cylinder0', .9)]","([('wall', 1.5)] + ([('cylinder0', .9)] if cfg.obstacle_cylinder_count else []))")
exec(compile(source,'reused_wall_geometry','exec'))
def differences(a,b,path=''):
 if isinstance(a,dict) and isinstance(b,dict):
  return sum([differences(a.get(k),b.get(k),path+'.'+k) for k in set(a)|set(b)],[])
 return [] if str(a)==str(b) else [path]
def main():
 torch.set_num_threads(2)
 c3,c4=config.CarryBoxWalled3EnvCfg(),config.CarryBoxWalled4EnvCfg()
 d=differences(c3.to_dict(),c4.to_dict());allowed=('.walled_variant','.obstacle_cylinder_count','.scene.cylinder','.scene.depth_camera.object_names')
 assert d and all(any(v.startswith(prefix) for prefix in allowed) for v in d),d
 a3,a4=config.CarryBoxWalled3PPORunnerCfg(),config.CarryBoxWalled4PPORunnerCfg()
 assert set(differences(a3.to_dict(),a4.to_dict()))=={'.experiment_name','.run_name'}
 assert CarryBoxPPORunnerCfg().policy.init_noise_std==.5 and CarryBoxPPORunnerCfg().algorithm.entropy_coef==.005
 cfg=c3 if args.variant==3 else c4;cfg.scene.num_envs=4;cfg.seed=42;cfg.sim.device=args.device
 agent=a3 if args.variant==3 else a4
 env=gym.make(f'Template-Perceptual-Ball-CarryBox-Walled{args.variant}-v0',cfg=cfg)
 try:
  b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);report=dict(config_differences=d,rsi={},depth_changes={})
  geometry(b,w,cfg,report)
  cfg.reference_init=True;cfg.search_prob=.02;cfg.reset_skill_probabilities=(.6,.3,.1)
  with torch.inference_mode():
   robot=b.scene['robot'];s=task.state(b)
   for skill in range(3):
    cfg.reset_skill_probabilities=tuple(float(i==skill) for i in range(3));obs,_=w.reset()
    local_com=robot.data.body_com_pos_b[:,s.head]
    expected=robot.data.body_link_pos_w[:,s.head]+quat_apply(robot.data.body_link_quat_w[:,s.head],local_com)
    torch.testing.assert_close(task.head_height(b),expected[:,2]-b.scene.env_origins[:,2],atol=1e-5,rtol=0)
    if skill==2:assert (task.head_height(b)>.95).all(),task.head_height(b)
    base=robot.data.root_pos_w[:,2]-b.scene.env_origins[:,2]
    assert not (task.fallen(b)&(base>=.2)&(task.head_height(b)>=.4)).any()
    # Both physical action bounds and original raw observation semantics.
    action=b.action_manager.get_term('joint_pos');action.process_actions(torch.full((4,29),50.,device=args.device))
    hard=robot.data.joint_pos_limits
    assert (action.processed_actions<=hard[...,1]+1e-6).all()
    assert (action.processed_actions>=hard[...,0]-1e-6).all()
    assert (action.raw_actions==50).all()
    if skill==1:
     platform=task.obstacle_pose(b,'platform')[:,2]+.4
     bottom=base_task.lift_geometry(b)[0]+b.scene.env_origins[:,2]
     assert (platform<=bottom+1e-4).all()
   # Hold reference penalty must eliminate the conflicting knee soft lower penalty.
   ids=joint_mapping(robot.joint_names);inverse=torch.argsort(torch.tensor(ids,device=args.device))
   saved=robot.data.joint_pos.clone();q=s.library.clips[s.library.clip_groups.index('carryWith')][0][20]
   robot.data.joint_pos[:]=q[inverse]
   cost=5*task.reference_joint_pos_limits(b);assert (cost<.01).all(),cost
   robot.data.joint_pos[:]=saved
   report['hold_reference_penalty']=cost.tolist()
   cfg.reset_skill_probabilities=(.6,.3,.1);obs,_=w.reset()
  runner=CarryBoxOnPolicyRunner(w,agent.to_dict(),log_dir=str(OUT/'train'),device=args.device)
  torch.testing.assert_close(runner.alg.policy.log_std.exp(),torch.full((29,),.2,device=args.device))
  old=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_21-08-12_wall4_handoff_v6_amp15_20261014_210808/model_13600.pt'
  try:runner.load(str(old));raise AssertionError('old contract accepted')
  except ValueError:pass
  before=copy.deepcopy(runner.alg.policy.state_dict());runner.learn(3,init_at_random_ep_len=False)
  assert any(not torch.equal(before[k],v) for k,v in runner.alg.policy.state_dict().items())
  assert all(torch.isfinite(v).all() for v in runner.alg.policy.state_dict().values())
  runner.save(str(OUT/'model.pt'))
  fresh=CarryBoxOnPolicyRunner(w,agent.to_dict(),log_dir=str(OUT/'resumed'),device=args.device);fresh.load(str(OUT/'model.pt'));fresh.learn(1,init_at_random_ep_len=False)
  obs=w.get_observations();export_depth_policy(fresh.alg.policy,obs,str(OUT/'export'))
  assert b.checkpoint_contract()['migration_revision']==7
  assert 'Skill/loco_episodes' in b.extras['log'] and 'Control/physical_target_clipped_fraction' in b.extras['log']
  report.update(status='PASS',revision=7,iterations=4,finite=True,export=True,contract=b.checkpoint_contract(),head_reference='COM',mesh_count=len(b.scene['depth_camera'].mesh_manifest),reset_counts=s.episode_counts.tolist())
  (OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('WALL_PARITY_PASS',flush=True)
 finally:env.close()
try:main()
finally:app.close(wait_for_replicator=False)
