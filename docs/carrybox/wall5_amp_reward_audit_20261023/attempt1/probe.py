"""Frozen policies/AMP, matched initial states; production remains untouched."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['current','rev22','no_delay'],required=True)
AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
from pathlib import Path
from types import SimpleNamespace
import hashlib,json
import numpy as np
import torch
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import wrap_to_pi
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task,carrybox_walled as common
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox as base
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic,Wall5AMP,CarryBoxWall5PPO
from perceptual_ball.carrybox_wall5 import Wall5MotionLibrary
D=Path(__file__).resolve().parent;R=D.parents[2];S=json.loads((D/'selection.json').read_text());N=32
def cpu(x):return x.detach().cpu().numpy().copy()
def stats(x):
 x=x.float().flatten();return dict(n=len(x),mean=float(x.mean()),median=float(x.median()),p05=float(torch.quantile(x,.05)),p95=float(torch.quantile(x,.95)),zero_fraction=float((x<=1e-8).float().mean()))
def main():
 torch.set_num_threads(2)
 ck=torch.load(S['checkpoint'],map_location=args.device,weights_only=False);old=torch.load(S['baseline_checkpoint'],map_location=args.device,weights_only=False)
 cfg,agent=CarryBoxWalled5EnvCfg(),CarryBoxWalled5PPORunnerCfg();cfg.scene.num_envs=N;cfg.seed=42;cfg.sim.device=args.device
 for k in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,k,262144)
 env=task.Wall5CarryBoxEnv(cfg=cfg)
 try:
  assert env.checkpoint_contract()==ck['environment_contract']
  wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=wrapped.reset()
  pc=agent.policy.to_dict();pc.pop('class_name');policy=CarryBoxWall5ActorCritic(obs,agent.obs_groups,29,**pc).to(args.device)
  policy.load_state_dict((old if args.mode=='rev22' else ck)['model_state_dict'],strict=True);policy.eval()
  discs={}
  for label,c in [('current',ck),('old',old)]:
   disc=Wall5AMP(600).to(args.device);disc.load_state_dict(c['amp']['model'],strict=True);disc.eval();discs[label]=disc
  saved={k:v.clone() for k,v in policy.state_dict().items()};saved_d={label:{k:v.clone() for k,v in d.state_dict().items()} for label,d in discs.items()}
  # Actual reward-mixing code executes with a one-step, read-only audit buffer.
  harness=SimpleNamespace(_ensure_motion_library=lambda:None,device=env.device,storage=SimpleNamespace(step=0),amp=discs['current'],amp_config=ck['amp']['config'],amp_rollout=torch.zeros(1,N,600,device=env.device),amp_valid=torch.zeros(1,N,device=env.device,dtype=torch.bool))
  library=Wall5MotionLibrary(device=env.device,env_fps=50.)
  assert library.metadata==ck['amp']['dataset']
  env.set_training_iteration(0);env.set_training_iteration(ck['iter'])
  robot=env.scene['robot'];s=common.state(env);term=env.action_manager.get_term('joint_pos')
  physical=[];active=False;last_time=None
  original_update=env.scene.update
  def update(dt):
   nonlocal last_time
   result=original_update(dt)
   if active and getattr(env,'_carrybox_in_step',False):
    data=robot.data
    if last_time is not None:assert abs(data._sim_timestamp-last_time-.005)<1e-7
    last_time=data._sim_timestamp
    physical.append(dict(qd=cpu(data.joint_vel),target=cpu(data.joint_pos_target),root_velocity=cpu(data.root_link_lin_vel_w)))
   return result
  env.scene.update=update
  with torch.inference_mode():
   torch.manual_seed(73);obs,_=wrapped.reset();env.episode_length_buf.zero_()
   initial=dict(root=robot.data.root_state_w.clone().cpu(),q=robot.data.joint_pos.clone().cpu(),qd=robot.data.joint_vel.clone().cpu(),
    stiffness=robot.data.joint_stiffness.clone().cpu(),damping=robot.data.joint_damping.clone().cpu(),delay=term.delay.index.clone().cpu(),delay_buffer=term.delay.buffer.clone().cpu(),materials=robot.root_physx_view.get_material_properties().clone().cpu())
   for k,v in obs.items():initial['obs_'+k]=v.clone().cpu()
   for k,v in env.scene.rigid_objects.items():initial['object_'+k]=v.data.root_state_w.clone().cpu()
   for i,v in enumerate(env.event_manager._interval_term_time_left):initial['timer_'+str(i)]=v.clone().cpu()
   torch.save(initial,D/f'{args.mode}_initial.pt')
   if args.mode!='current':
    ref=torch.load(D/'current_initial.pt',weights_only=False)
    assert initial.keys()==ref.keys()
    for k,v in initial.items():torch.testing.assert_close(v,ref[k],atol=2e-5,rtol=1e-5,msg=k)
   if args.mode=='no_delay':term.delay.index.fill_(4)
   kinds=torch.where(s.default_reset,0,s.skills+1).clone();initial_xy=(env.scene['box'].data.root_pos_w[:,:2]-robot.data.root_link_pos_w[:,:2]).norm(dim=-1)
   finished=torch.zeros(N,device=env.device,dtype=torch.bool);length=torch.full((N,),1000,device=env.device,dtype=torch.long)
   causes={name:torch.zeros(N,device=env.device,dtype=torch.bool) for name in env.termination_manager.active_terms}
   rows=[];active=True
   for step in range(1000):
    live=~finished;actions=policy.act_inference(obs)
    obs,reward,done,extra=wrapped.step(actions)
    assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
    mixed=CarryBoxWall5PPO._process_amp(harness,obs,reward,done,extra)
    motion=harness.amp_rollout[0];style=discs['current'].predict_reward(motion);oldstyle=discs['old'].predict_reward(motion);logit=discs['current'](motion).squeeze(-1)
    torch.testing.assert_close(mixed,.75*reward+.125*style,atol=1e-7,rtol=1e-6);assert harness.amp_valid.all()
    rewards=env.reward_manager._step_reward*env.step_dt;torch.testing.assert_close(rewards.sum(-1),reward,atol=1e-6,rtol=1e-5)
    new=live&done.bool();length[new]=step+1
    for name in causes:causes[name][new]=env.termination_manager.get_term(name)[new]
    finished|=done.bool();valid=live&~done.bool()
    data,box=robot.data,env.scene['box'].data;delta=box.root_pos_w-data.root_link_pos_w;xy=delta[:,:2].norm(dim=-1);xyz=delta.norm(dim=-1)
    towards=(delta[:,:2]/xy.clamp_min(1e-6)[:,None]*data.root_link_lin_vel_w[:,:2]).sum(-1)
    bearing=wrap_to_pi(torch.atan2(delta[:,1],delta[:,0])-common.heading(data.root_link_quat_w)).abs()
    oldtowards=(delta[:,:2]/xy.clamp_min(1e-6)[:,None]*data.root_com_lin_vel_w[:,:2]).sum(-1)
    legacy=torch.where(xyz<old['environment_contract']['reward_geometry']['near_distance'],1.5,torch.exp(-5*(.85-oldtowards).square())+.5*torch.exp(-.75*bearing))*.02
    g=task.grasp_state(env);force=torch.stack([env.scene[f'{side}_box_contact'].data.force_matrix_w.flatten(1,-2).norm(dim=-1).amax(-1) for side in ('left','right')],-1)
    torch.testing.assert_close(g['walk_task'][valid]*.02,rewards[valid,env.reward_manager.active_terms.index('walk_task')],atol=1e-6,rtol=1e-5)
    torch.testing.assert_close(g['carryup_task'][valid]*.02,rewards[valid,env.reward_manager.active_terms.index('carryup_task')],atol=1e-6,rtol=1e-5)
    values=dict(valid=valid,live=live,done=done,xy=xy,xyz=xyz,towards=towards,speed=data.root_link_lin_vel_w[:,:2].norm(dim=-1),bearing=bearing,
      travel=((xy-.6)/.2).clamp(0,1),reach_gate=((.98-xyz)/.08).clamp(0,1),reach=g['reach'],bilateral=g['bilateral'],lift=g['lift'],contact_force=force,
      rewards=rewards,task=reward,style=style,old_style=oldstyle,logit=logit,mixed=mixed,old_walk=legacy,
      action=actions,target=term.processed_actions,saturation=term.target_saturation,bottom=base.lift_geometry(env)[0],root=data.root_link_pos_w)
    rows.append({k:cpu(v) for k,v in values.items()})
    if (step+1)%250==0:print('PROBE_PROGRESS',args.mode,step+1,flush=True)
   active=False
   assert len(physical)==4000
   np.savez_compressed(D/f'{args.mode}_trajectory.npz',**{k:np.stack([x[k] for x in rows]) for k in rows[0]})
   np.savez_compressed(D/f'{args.mode}_physical.npz',**{k:np.stack([x[k] for x in physical]) for k in physical[0]})
   expert,clips=library.sample_expert_amp_obs(4096,return_clip_ids=True)
   expert_scores={}
   for group in set(library.clip_groups):
    mask=torch.tensor([library.clip_groups[i]==group for i in clips.tolist()],device=env.device)
    expert_scores[group]=dict(style=stats(discs['current'].predict_reward(expert[mask])),logit=stats(discs['current'](expert[mask])))
   for k,v in policy.state_dict().items():assert torch.equal(v,saved[k])
   for label,d in discs.items():
    for k,v in d.state_dict().items():assert torch.equal(v,saved_d[label][k])
  result=dict(status='PASS',mode=args.mode,num_envs=N,initial_kinds=kinds.tolist(),initial_xy=initial_xy.tolist(),first_episode_steps=length.tolist(),
    first_episode_causes={k:v.tolist() for k,v in causes.items()},first_censored=(~finished).tolist(),reward_names=env.reward_manager.active_terms,joint_names=robot.joint_names,
    action_joint_names=[robot.joint_names[i] for i in term._joint_ids],expert_scores=expert_scores,physics_hz=200,policy_hz=50,weights_unchanged=True,amp_mixing_verified=True,
    checkpoint=S['baseline_checkpoint'] if args.mode=='rev22' else S['checkpoint'],old_policy_weights_only=args.mode=='rev22',diagnostic_overrides=['same current rev28 environment, seed73 reset, iteration4800']+(['delay index4'] if args.mode=='no_delay' else []))
  (D/f'{args.mode}.json').write_text(json.dumps(result,indent=2)+'\n');print('PROBE_PASS',args.mode,flush=True)
 finally:env.close()
try:main()
except BaseException:
 import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
