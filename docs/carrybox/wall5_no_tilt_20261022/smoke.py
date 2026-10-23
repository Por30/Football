"""Verify revision25 angle removal, remaining boundaries, PPO/AMP and restore."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser);args=parser.parse_args();app=AppLauncher(args).app
import copy,json,hashlib
from pathlib import Path
import torch,gymnasium as gym
import perceptual_ball.tasks
from isaaclab.utils.math import quat_from_euler_xyz
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled3EnvCfg,CarryBoxWalled4EnvCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_wall5 import tipped
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
D=Path(__file__).resolve().parent;R=D.parents[2]

def main():
 torch.set_num_threads(2)
 cfg,agent=CarryBoxWalled5EnvCfg(),CarryBoxWalled5PPORunnerCfg()
 assert cfg.terminations.tipped is None and cfg.episode_length_s==20.
 for cls in (CarryBoxWalled3EnvCfg,CarryBoxWalled4EnvCfg):assert cls().terminations.tipped is not None
 cfg.scene.num_envs=32;cfg.seed=42;cfg.sim.device=args.device
 for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
  setattr(cfg.sim.physx,name,262144)
 env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
 try:
  b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=w.reset()
  terms=set(b.termination_manager.active_terms)
  assert terms=={'time_out','invalid','fell_pelvis','fell_head','fell_hip','box_speed'},terms
  robot=b.scene['robot'];box=b.scene['box'];manager=b.termination_manager
  with torch.inference_mode():
   # Lift the whole robot clear of height/contact thresholds to isolate angles.
   root=robot.data.root_state_w.clone();root[:,:3]=b.scene.env_origins;root[:,2]+=2.
   roll=torch.zeros(32,device=b.device);pitch=roll.clone();zero=roll.clone()
   roll[:2]=torch.tensor([.6,-.6],device=b.device);pitch[2:4]=torch.tensor([1.2,-1.2],device=b.device)
   root[:,3:7]=quat_from_euler_xyz(roll,pitch,zero);root[:,7:]=0.
   robot.write_root_state_to_sim(root);box.write_root_velocity_to_sim(torch.zeros(32,6,device=b.device))
   b.sim.forward();b.episode_length_buf.zero_()
   assert tipped(b)[:4].all(),'Probe did not exceed old roll/pitch thresholds'
   assert not manager.compute().any(),'An isolated large angle still resets'
   # Zero quaternion angles and change only the whole-robot height.
   root[:,3:7]=torch.tensor([1.,0.,0.,0.],device=b.device);root[:,2]=b.scene.env_origins[:,2]-2.
   robot.write_root_state_to_sim(root);b.sim.forward()
   for key in ('fell_pelvis','fell_head','fell_hip'):
    term=getattr(b.cfg.terminations,key);assert term.func(b,**term.params).all(),key
   assert manager.compute().all() and manager.terminated.all()
   # Each existing strict boundary remains covered by its existing unit test;
   # isolate box speed and timeout here in the live termination manager.
   root[:,2]=b.scene.env_origins[:,2]+2.;robot.write_root_state_to_sim(root);b.sim.forward()
   vel=torch.zeros(32,6,device=b.device);vel[:2,0]=torch.tensor([3.01,2.99],device=b.device)
   box.write_root_velocity_to_sim(vel)
   done=manager.compute();assert done[0] and not done[1:].any()
   box.write_root_velocity_to_sim(torch.zeros_like(vel));b.episode_length_buf[:]=b.max_episode_length
   assert manager.compute().all() and manager.time_outs.all() and not manager.terminated.any()
   obs,_=w.reset();b.episode_length_buf.zero_()
  shapes={k:list(v.shape) for k,v in obs.items()}
  assert shapes=={'proprio':[32,372],'perception':[32,4,27,48],'amp':[32,600],'box_pose_target':[32,10],'critic_state':[32,123],'action_bounds':[32,58]},shapes
  contract=b.checkpoint_contract();assert contract['migration_revision']==25
  oldrun=Path(json.loads((D/'before.json').read_text())['old_run']);oldpath=oldrun/'model_0.pt'
  old=torch.load(oldpath,map_location='cpu',weights_only=False)['environment_contract']
  changed={k for k in contract.keys()|old.keys() if contract.get(k)!=old.get(k)}
  assert changed=={'migration_revision','roll_termination','roll_limit','termination_profile','failure_diagnostics'},changed
  profile_delta={k for k in contract['termination_profile'] if contract['termination_profile'][k]!=old['termination_profile'][k]}
  assert profile_delta=={'roll_rad','pitch_rad'} and contract['roll_limit'] is None
  runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device)
  before=copy.deepcopy(runner.alg.policy.state_dict());before_amp=copy.deepcopy(runner.alg.amp.state_dict()) if hasattr(runner.alg,'amp') else None
  with torch.inference_mode():
   for step in range(agent.num_steps_per_env):
    if step==0:b.episode_length_buf[[0,3]]=b.max_episode_length-1
    action=runner.alg.act(obs);obs,reward,done,extra=w.step(action)
    runner.alg.process_env_step(obs,reward,done,extra)
    assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
    if step==0:
     assert done[[0,3]].all()
     assert extra['terminal_observations']['obs']['critic_state'].shape[-1]==123
     assert 'Skill/loco_tilt_at_episode_end_fraction' in extra['log']
     assert 'Skill/loco_tipped_fraction' not in extra['log']
   runner.alg.compute_returns(obs)
  loss=runner.alg.update();assert all(torch.isfinite(torch.tensor(v)) for v in loss.values()),loss
  for prefix in ('actor.','critic.','perception_encoder.','pose_head.'):
   assert any(not torch.equal(before[k],v) for k,v in runner.alg.policy.state_dict().items() if k.startswith(prefix)),prefix
  runner.current_learning_iteration=1;path=D/'smoke_model.pt';runner.save(path)
  saved=torch.load(path,map_location='cpu',weights_only=False)
  assert saved['amp']['dataset']['clip_count']==15
  for opt in (saved['optimizer_state_dict'],saved['amp']['optimizer']):
   assert {int(v['step']) for v in opt['state'].values()}=={20}
  restored=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device);restored.load(path)
  with torch.inference_mode():
   torch.testing.assert_close(restored.alg.policy.act_inference(obs),runner.alg.policy.act_inference(obs),atol=0,rtol=0)
  try:restored.load(oldpath)
  except ValueError as error:assert 'environment variant/contract' in str(error)
  else:raise AssertionError('Revision24 strict restore was accepted')
  before_hash=json.loads((D/'before.json').read_text())['source_sha256']
  allowed={'source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py','source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py'}
  actual={p for p,h in before_hash.items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h}
  assert actual==allowed,actual
  result=dict(status='PASS',num_envs=32,active_terminations=sorted(terms),isolated_angle_cases_rad={'roll':[.6,-.6],'pitch':[1.2,-1.2]},angle_cases_reset=False,height_conditions_active=True,box_speed_boundary=True,timeout_steps=b.max_episode_length,shapes=shapes,contract=contract,contract_changed_keys=sorted(changed),loss=loss,ppo_amp_updates=1,restore=True,revision24_restore_rejected=True,other_sources_unchanged=True)
  (D/'smoke.json').write_text(json.dumps(result,indent=2)+'\n');print('NO_TILT_SMOKE_PASS',flush=True)
 finally:env.close()
try:main()
except BaseException:
 import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
