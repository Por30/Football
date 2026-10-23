"""Quota regression: grounded resets, paired buffers, PPO/AMP and finite fresh pilot."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
from pathlib import Path
import ast,copy,json,hashlib,time
import torch,gymnasium as gym
import perceptual_ball.tasks
from isaaclab.utils.math import quat_apply,quat_conjugate,yaw_quat
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as common
from perceptual_ball.carrybox_physhsi import interpolate,fixed_hybrid
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
D=Path(__file__).resolve().parent;R=D.parents[2];N=512
# Reuse the already established collider/paired-reference and partial-reset
# assertions; no simulation or main routine is executed while loading it.
tree=ast.parse((R/'docs/carrybox/wall5_groundfix_20261022/smoke.py').read_text())
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='check_ground')
exec(compile(ast.Module(body=[node],type_ignores=[]),'reused-ground-check','exec'),globals())

def main():
 torch.set_num_threads(2)
 cfg,agent=CarryBoxWalled5EnvCfg(),CarryBoxWalled5PPORunnerCfg();cfg.scene.num_envs=N;cfg.seed=42;cfg.sim.device=args.device
 for k in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,k,262144)
 env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
 try:
  b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=w.reset();s=common.state(b)
  expected_skill,expected_default=fixed_hybrid(torch.arange(N,device=b.device),N,.8,cfg.reset_skill_probabilities)
  expected_labels=torch.where(expected_default,0,expected_skill+1)
  expected_counts=torch.bincount(expected_labels,minlength=4)
  with torch.inference_mode():
   reset_rows=check_ground(b,w)
   torch.testing.assert_close(s.skills,expected_skill);torch.testing.assert_close(s.default_reset,expected_default)
   obs,_=w.reset();b.episode_length_buf.zero_()
  shapes={k:list(v.shape) for k,v in obs.items()}
  assert shapes=={'proprio':[N,372],'perception':[N,4,27,48],'amp':[N,600],'box_pose_target':[N,10],'critic_state':[N,123],'action_bounds':[N,58]},shapes
  contract=b.checkpoint_contract();assert contract['migration_revision']==27
  before=json.loads((D/'before.json').read_text())
  old=torch.load(before['checkpoint'],map_location='cpu',weights_only=False)['environment_contract']
  changed={k for k in contract.keys()|old.keys() if contract.get(k)!=old.get(k)}
  assert changed=={'migration_revision','reset_assignment','reset_default_probability','reset_total_probabilities','reset_quota_scope'},changed
  # Float arithmetic may differ at 0.2 by one ulp; proportions are unchanged.
  torch.testing.assert_close(torch.tensor(contract['reset_total_probabilities']),torch.tensor(old['reset_total_probabilities']),atol=1e-7,rtol=0)
  runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device)
  initial=copy.deepcopy(runner.alg.policy.state_dict());updates=[];ended=[[] for _ in range(4)];steps=torch.zeros(N,device=b.device,dtype=torch.long)
  start=time.monotonic()
  for iteration in range(128):
   b.set_training_iteration(iteration)
   with torch.inference_mode():
    for step in range(agent.num_steps_per_env):
     if iteration==0 and step==0:b.episode_length_buf[[0,N-1]]=b.max_episode_length-1
     action=runner.alg.act(obs);obs,reward,done,extra=w.step(action);steps+=1
     runner.alg.process_env_step(obs,reward,done,extra)
     assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
     torch.testing.assert_close(s.skills,expected_skill);torch.testing.assert_close(s.default_reset,expected_default)
     for i,name in enumerate(('loco','pickup','hold')):
      torch.testing.assert_close(extra['log'][f'Sampling/{name}_transition_fraction'],(expected_skill==i).float().mean())
     torch.testing.assert_close(extra['log']['Sampling/default_transition_fraction'],expected_default.float().mean())
     for i in range(4):ended[i].extend(steps[done.bool()&(expected_labels==i)].tolist())
     steps[done.bool()]=0
     if iteration==0 and step==0:
      assert done[[0,N-1]].all()
      assert extra['terminal_observations']['obs']['critic_state'].shape[-1]==123
    runner.alg.compute_returns(obs)
   loss=runner.alg.update();assert all(torch.isfinite(torch.tensor(v)) for v in loss.values()),loss
   for model in (runner.alg.policy,runner.alg.amp):assert all(torch.isfinite(v).all() for v in model.state_dict().values())
   row=dict(iteration=iteration,loss=loss,elapsed_s=time.monotonic()-start,
    recent_completed_steps={label:(sum(values[-200:])/len(values[-200:]) if values else None) for label,values in zip(('default','loco','pickup','hold'),ended)},
    transition_counts=expected_counts.tolist())
   updates.append(row)
   if iteration%16==0 or iteration==127:
    (D/'pilot_progress.json').write_text(json.dumps(row,indent=2)+'\n');print('PILOT',json.dumps(row),flush=True)
  for prefix in ('actor.','critic.','perception_encoder.','pose_head.'):
   assert any(not torch.equal(initial[k],v) for k,v in runner.alg.policy.state_dict().items() if k.startswith(prefix)),prefix
  runner.current_learning_iteration=128;path=D/'pilot_model.pt';runner.save(path)
  saved=torch.load(path,map_location='cpu',weights_only=False)
  assert saved['amp']['dataset']['clip_count']==15
  for opt in (saved['optimizer_state_dict'],saved['amp']['optimizer']):assert {int(v['step']) for v in opt['state'].values()}=={2560}
  restored=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device);restored.load(path)
  with torch.inference_mode():torch.testing.assert_close(restored.alg.policy.act_inference(obs),runner.alg.policy.act_inference(obs),atol=0,rtol=0)
  try:restored.load(before['checkpoint'])
  except ValueError as e:assert 'environment variant/contract' in str(e)
  else:raise AssertionError('Old revision strict restore accepted')
  result=dict(status='PASS',num_envs=N,contract=contract,contract_changed_keys=sorted(changed),shapes=shapes,
   ground_reset_cases=len(reset_rows),minimum_reset_clearance_m=min(r['after_m'] for r in reset_rows),
   all_three_pickups=True,partial_reset_unchanged=True,reset_delay_fill_final_q=True,
   fresh_updates=128,transition_counts=expected_counts.tolist(),updates=updates,
   restore_identical=True,revision26_strict_restore_rejected=True,convergence_evaluated=False)
  (D/'smoke.json').write_text(json.dumps(result,indent=2)+'\n');print('STABILITY_VALIDATION_PASS',flush=True)
 finally:env.close()
try:main()
except BaseException:
 import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
