"""Revision24 live geometry/reset/delay, PPO+AMP, strict restore and export."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser);args=parser.parse_args();app=AppLauncher(args).app
import copy,json,hashlib
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled3EnvCfg,CarryBoxWalled4EnvCfg,WalledJointPositionAction
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as parent,carrybox_physhsi as phy
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy
D=Path(__file__).resolve().parent


def geometry(env):
 from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema
 stage=env.sim.get_initial_stage();root=stage.GetPrimAtPath('/World/envs/env_0/Robot')
 pelvis=root.GetChild('pelvis')
 assert not any(p.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get()
                for p in Usd.PrimRange(pelvis,Usd.TraverseInstanceProxies()))
 shapes=[];capsules=[];leaves={'Mesh':0,'Cube':0,'Capsule':0,'Cylinder':0}
 for p in Usd.PrimRange(root,Usd.TraverseInstanceProxies()):
  assert 'full_body_collisions' not in str(p.GetPath())
  if p.HasAPI(PhysxSchema.PhysxArticulationAPI):
   assert PhysxSchema.PhysxArticulationAPI(p).GetEnabledSelfCollisionsAttr().Get() is True
  if p.HasAPI(UsdPhysics.FilteredPairsAPI):
   assert not UsdPhysics.FilteredPairsAPI(p).GetFilteredPairsRel().GetTargets()
  if '/collisions/' in str(p.GetPath()) and p.GetTypeName() in leaves:leaves[p.GetTypeName()]+=1
  if p.GetName()=='collisions' and p.HasAPI(UsdPhysics.CollisionAPI):shapes.append(str(p.GetPath()))
  if p.IsA(UsdGeom.Capsule) and '/collisions/' in str(p.GetPath()):
   c=UsdGeom.Capsule(p);capsules.append({'path':str(p.GetPath()),'radius':c.GetRadiusAttr().Get(),'height':c.GetHeightAttr().Get(),'axis':c.GetAxisAttr().Get()})
 assert len(shapes)==28,(len(shapes),shapes)
 assert len(capsules)==4,capsules
 assert leaves=={'Mesh':22,'Cube':4,'Capsule':4,'Cylinder':0},leaves
 assert all(abs(x['radius']-.03)<1e-6 and x['axis']=='Z' for x in capsules)
 for side in ('left','right'):
  link=root.GetChild(side+'_knee_link');c=link.GetChild('collisions')
  assert len([p for p in Usd.PrimRange(c,Usd.TraverseInstanceProxies()) if p.IsA(UsdGeom.Cube)])==2
 assert 'undesired_contacts' not in env.reward_manager.active_terms
 return dict(collision_links=len(shapes),shape_counts=leaves,capsules=capsules,self_collisions=True,new_pelvis_hull=False,contact_penalty=False)


def check_reset(env):
 s=parent.state(env);r=env.scene['robot'];term=env.action_manager.get_term('joint_pos')
 ids=torch.tensor([61,3,29,5,47,12,31],device=env.device)
 survivors=torch.tensor([0,1,2,4,6],device=env.device)
 oldr=r.data.root_state_w[survivors].clone();oldq=r.data.joint_pos[survivors].clone();oldbuf=term.delay.buffer[:,survivors].clone()
 env._reset_idx(ids)
 torch.testing.assert_close(r.data.root_state_w[survivors],oldr)
 torch.testing.assert_close(r.data.joint_pos[survivors],oldq)
 torch.testing.assert_close(term.delay.buffer[:,survivors],oldbuf)
 torch.testing.assert_close(r.data.root_vel_w[ids],s.reset_root_velocity[ids],atol=2e-5,rtol=1e-5)
 torch.testing.assert_close(r.data.joint_pos[ids],s.reset_joint_position[ids])
 torch.testing.assert_close(r.data.joint_vel[ids],s.reset_joint_velocity[ids])
 soft=r.data.soft_joint_pos_limits[ids]
 assert (r.data.joint_pos[ids]>=soft[...,0]-1e-6).all() and (r.data.joint_pos[ids]<=soft[...,1]+1e-6).all()
 q=r.data.joint_pos[ids][:,term._joint_ids]
 torch.testing.assert_close(term.delay.buffer[:,ids],q[None].expand(5,-1,-1))
 torch.testing.assert_close(term.processed_actions[ids],q)
 caps=torch.where(s.default_reset[ids],.5,.2)
 assert (r.data.root_vel_w[ids].abs()<=caps[:,None]+1e-5).all()
 assert (s.reset_joint_velocity[ids[s.default_reset[ids]]]==0).all()
 return {'partial_unsorted_reset':True,'root_com_velocity_readback':True,'buffer_prefill':True}


def main():
 torch.set_num_threads(2)
 cfg,agent=CarryBoxWalled5EnvCfg(),CarryBoxWalled5PPORunnerCfg()
 for cls in (CarryBoxWalled3EnvCfg,CarryBoxWalled4EnvCfg):
  other=cls();assert not other.scene.robot.spawn.articulation_props.enabled_self_collisions
  assert other.actions.joint_pos.class_type is WalledJointPositionAction
  assert other.rewards.undesired_contacts is not None
  assert other.reset_skill_probabilities==(.6,.3,.1)
 cfg.scene.num_envs=64;cfg.seed=42;cfg.sim.device=args.device
 for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
  setattr(cfg.sim.physx,name,262144)
 env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
 try:
  b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=w.reset()
  assert set(b.termination_manager.active_terms)=={'time_out','invalid','tipped','fell_pelvis','fell_head','fell_hip','box_speed'}
  g=geometry(b)
  s=parent.state(b);seen=set();origins=[];support_seen=0
  with torch.inference_mode():
   for _ in range(10):
    w.reset();s=parent.state(b)
    seen.update(s.reference_clip[s.skills==1].tolist())
    support_seen+=int(s.support_active.sum())
    assert all(torch.isfinite(v).all() for v in obs.values())
    origins.append({'default':int(s.default_reset.sum()),'loco_rsi':int(((s.skills==0)&~s.default_reset).sum()),'pickup':int((s.skills==1).sum()),'hold':int((s.skills==2).sum())})
    # Every reference clip uses its continuous frame time and stored qdot.
    for clip in s.reference_clip.unique().tolist():
     if clip<0:continue
     ids=(s.reference_clip==clip).nonzero().flatten()
     from perceptual_ball.carrybox_physhsi import interpolate
     from perceptual_ball.carrybox_amp import joint_mapping
     inverse=torch.argsort(torch.tensor(joint_mapping(b.scene['robot'].joint_names),device=b.device))
     expected=interpolate(s.references[clip]['joint_velocity'].float(),s.reference_time[ids])[:,inverse]
     torch.testing.assert_close(b.scene['robot'].data.joint_vel[ids],expected)
     expected_z=interpolate(s.references[clip]['base_height'].float(),s.reference_time[ids])+.05
     torch.testing.assert_close(b.scene['robot'].data.root_link_pos_w[ids,2]-b.scene.env_origins[ids,2],expected_z)
   assert len(seen)==3 and support_seen>0,(seen,support_seen)
   check=check_reset(b)
   old_steps=b.action_manager.get_term('joint_pos').delay.steps
   obs,reward,done,extras=w.step(torch.zeros(64,29,device=b.device))
   assert b.action_manager.get_term('joint_pos').delay.steps-old_steps==4
   assert all(torch.isfinite(v).all() for v in obs.values())
   initial_causes={k:int(getattr(phy,k)(b).sum()) for k in ('fallen_pelvis','fallen_head','fallen_hip','box_speed')}
   obs,_=w.reset()
  shapes={k:list(v.shape) for k,v in obs.items()}
  assert shapes=={'proprio':[64,372],'perception':[64,4,27,48],'amp':[64,600],'box_pose_target':[64,10],'critic_state':[64,123],'action_bounds':[64,58]},shapes
  assert obs['perception'].min()>=.1 and obs['perception'].max()<=3.
  assert any(x['root'].endswith('/Platform') for x in b.scene['depth_camera'].mesh_manifest)
  runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device)
  def update(current):
   nonlocal obs
   with torch.inference_mode():
    for step in range(agent.num_steps_per_env):
     if step==0:b.episode_length_buf[[0,3,7]]=b.max_episode_length-1
     action=current.alg.act(obs);obs,reward,done,extra=w.step(action)
     current.alg.process_env_step(obs,reward,done,extra)
     assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
     if step==0:
      assert done[[0,3,7]].all()
      term=extra['terminal_observations'];assert term['obs']['critic_state'].shape[-1]==123
    current.alg.compute_returns(obs)
   loss=current.alg.update();assert all(torch.isfinite(torch.tensor(v)) for v in loss.values());return loss
  before=copy.deepcopy(runner.alg.policy.state_dict());losses=[update(runner),update(runner)]
  for prefix in ('actor.','critic.','perception_encoder.','pose_head.'):
   assert any(not torch.equal(before[k],v) for k,v in runner.alg.policy.state_dict().items() if k.startswith(prefix))
  assert runner.alg.motion_metadata['clip_count']==15
  assert s.library.metadata['manifest_sha256']==runner.alg.motion_metadata['manifest_sha256']
  runner.current_learning_iteration=2;path=D/'smoke_model.pt';runner.save(path)
  restored=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device);restored.load(path)
  with torch.inference_mode():
   torch.testing.assert_close(restored.alg.policy.act_inference(obs),runner.alg.policy.act_inference(obs),atol=0,rtol=0)
   torch.testing.assert_close(restored.alg.policy.evaluate(obs),runner.alg.policy.evaluate(obs),atol=0,rtol=0)
  oldrun=Path(json.loads((D/'before.json').read_text())['old_run']);oldpath=oldrun/'model_0.pt'
  for optimizer in (True,False):
   try:restored.load(oldpath,load_optimizer=optimizer)
   except ValueError as error:assert 'environment variant/contract' in str(error)
   else:raise AssertionError('Old revision23 strict restore accepted')
  losses.append(update(restored))
  with torch.inference_mode():
   wrapper=export_depth_policy(restored.alg.policy,obs,D/'exported',{'depth_contract':b.depth_contract})
   expected=restored.alg.policy.act_inference(obs).cpu();flat,depth=obs['proprio'].cpu(),obs['perception'].cpu()
   torch.testing.assert_close(wrapper(flat,depth),expected,atol=2e-5,rtol=2e-5)
   loaded=torch.jit.load(str(D/'exported/policy.pt'));torch.testing.assert_close(loaded(flat,depth),expected,atol=2e-5,rtol=2e-5)
   assert not any(k.startswith(('critic.','pose_head.')) for k in loaded.state_dict())
  contract=b.checkpoint_contract();assert contract['migration_revision']==24
  assert contract['support_platform'] and contract['reset_reference_probability']==.8
  result=dict(status='PASS',geometry=g,reset=check,reset_counts=origins,pickup_clips_seen=sorted(seen),support_samples=support_seen,initial_causes=initial_causes,shapes=shapes,contract=contract,losses=losses,partial_reset=True,delay_updates_per_policy_step=4,strict_restore=True,old_restore_rejected=True,actor_export=True,other_variants_unchanged=True)
  (D/'smoke.json').write_text(json.dumps(result,indent=2)+'\n');print('PHYSHSI_SMOKE_PASS',flush=True)
 finally:env.close()
try:main()
except BaseException:
 import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
