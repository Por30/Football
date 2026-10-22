"""First-episode inference diagnostics; mutations are confined to this process."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--collision',choices=['on','off'],required=True)
AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import json,hashlib,statistics
from pathlib import Path
import torch
import omni.physics.tensors as physics
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import euler_xyz_from_quat,wrap_to_pi
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic,Wall5AMP
from perceptual_ball.tasks.manager_based.perceptual_ball import carrybox_wall5_env_cfg as config
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task,carrybox_walled as common

D=Path(__file__).resolve().parent;ROOT=D.parents[2];S=json.loads((D/'selection.json').read_text())
N=32;MAX_STEPS=1000

def main():
 torch.set_num_threads(2)
 cfg,agent=config.CarryBoxWalled5EnvCfg(),config.CarryBoxWalled5PPORunnerCfg()
 cfg.scene.num_envs=N;cfg.seed=42;cfg.sim.device=args.device
 cfg.scene.robot.spawn.articulation_props.enabled_self_collisions=args.collision=='on'
 for k in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,k,262144)
 current=torch.load(S['checkpoint'],map_location=args.device,weights_only=False)
 previous=torch.load(S['old_checkpoint'],map_location=args.device,weights_only=False)
 env=task.Wall5CarryBoxEnv(cfg=cfg)
 try:
  contract=env.checkpoint_contract();expected=dict(current['environment_contract']);expected['self_collisions']=args.collision=='on'
  assert contract==expected
  wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=wrapped.reset()
  policy_cfg=agent.policy.to_dict();policy_cfg.pop('class_name')
  policy=CarryBoxWall5ActorCritic(obs,agent.obs_groups,29,**policy_cfg).to(args.device);policy.eval()
  amp=Wall5AMP(600).to(args.device);amp.eval()
  env.set_training_iteration(0);env.set_training_iteration(current['iter'])
  robot=env.scene['robot'];state=common.state(env)
  physical=physics.create_simulation_view('torch');physical.set_subspace_roots('/')
  contact=physical.create_rigid_contact_view('/World/envs/env_0/Robot/*',filter_patterns=['/World/envs/env_0/Robot/'+n for n in robot.body_names],max_contact_data_count=4096)
  sensor_paths=list(contact.sensor_paths)
  active=False;ended={};push_count=torch.zeros(N,dtype=torch.long,device=env.device)
  first_contact_peak=None;physics_steps=0;contact_trace=[];step=0
  original_sim_step=env.sim.step
  def sim_step(*a,**kw):
   nonlocal first_contact_peak,physics_steps
   result=original_sim_step(*a,**kw)
   if active and 0 not in ended:
    forces=contact.get_contact_force_matrix(env.physics_dt).norm(dim=-1)
    first_contact_peak=forces.clone() if first_contact_peak is None else torch.maximum(first_contact_peak,forces)
    physics_steps+=1
    if float(forces.max())>10:
     ix=(forces>10).nonzero().tolist()
     contact_trace.append(dict(policy_step=step+1,physics_step=physics_steps,contacts=[dict(a=sensor_paths[i].rsplit('/',1)[-1],b=robot.body_names[j],force_n=float(forces[i,j])) for i,j in ix]))
   return result
  env.sim.step=sim_step
  def snapshot(i,censored=False):
   roll,pitch,_=euler_xyz_from_quat(robot.data.root_link_quat_w[i:i+1]);delta=env.scene['box'].data.root_pos_w[i]-robot.data.root_link_pos_w[i]
   return dict(env_id=i,skill=int(state.skills[i]),steps=int(state.actual_episode_steps[i]),censored=censored,
    tipped=bool(task.tipped(env)[i]),fell_pelvis=bool(common.fallen_pelvis(env)[i]),fell_head=bool(common.fallen_head(env)[i]),timeout=bool(env.termination_manager.time_outs[i]),
    roll=float(wrap_to_pi(roll)[0]),pitch=float(wrap_to_pi(pitch)[0]),root_height=float(robot.data.root_link_pos_w[i,2]-env.scene.env_origins[i,2]),head_height=float(common.head_height(env)[i]),
    speed=float(robot.data.root_link_lin_vel_w[i,:2].norm()),distance_xy=float(delta[:2].norm()),pushes=int(push_count[i]))
  original_reset=env._reset_idx
  def reset_capture(ids):
   if active and getattr(env,'_carrybox_in_step',False):
    for i in ids.tolist():
     if i not in ended:ended[i]=snapshot(i)
   original_reset(ids)
  env._reset_idx=reset_capture
  event=env.event_manager.get_term_cfg('push_robot');original_push=event.func;disable_push=False
  def push_capture(e,ids,**kw):
   if not disable_push:
    original_push(e,ids,**kw)
    if active:push_count[ids]+=1
  event.func=push_capture;env.event_manager.set_term_cfg('push_robot',event)
  cases={};output=dict(status='RUNNING',self_collisions=args.collision=='on',num_envs=N,max_steps=MAX_STEPS,checkpoint=S['checkpoint'],previous_checkpoint=S['old_checkpoint'],cases=cases)
  with torch.inference_mode():
   for label,checkpoint,disable_push,hold_reset in [('current_push',current,False,False),('current_no_push',current,True,False),('previous_no_push',previous,True,False),('reset_angles_no_push',current,True,True)]:
    active=False;policy.load_state_dict(checkpoint['model_state_dict'],strict=True);amp.load_state_dict(checkpoint['amp']['model'],strict=True)
    saved={k:v.clone() for k,v in policy.state_dict().items()}
    torch.manual_seed(42);obs,_=wrapped.reset();ended.clear();push_count.zero_();physics_steps=0;first_contact_peak=None;contact_trace=[]
    loco_ids=(state.skills==0).nonzero().flatten().tolist();assert len(loco_ids)==24
    term=env.action_manager.get_term('joint_pos');hold_action=((robot.data.joint_pos[:,term._joint_ids]-term._offset)/term._scale).clone()
    initial=[snapshot(i,True) for i in loco_ids];initial_q=robot.data.joint_pos.clone();trace=[];reward_sum=None;count=0;action_abs=0.;style_sum=0.;step=0
    active=True
    for step in range(MAX_STEPS):
     ids=[i for i in loco_ids if i not in ended]
     if not ids:break
     action=hold_action if hold_reset else policy.act_inference(obs)
     assert torch.isfinite(action).all() and all(torch.isfinite(v).all() for v in obs.values())
     style_sum+=float(amp.predict_reward(obs['amp'][ids]).sum());action_abs+=float(action[ids].abs().mean(-1).sum());count+=len(ids)
     if 0 not in ended:
      q=robot.data.joint_pos[0];row=snapshot(0,True)
      row.update(joint_pos=q.tolist(),joint_vel=robot.data.joint_vel[0].tolist(),action=action[0].tolist(),default=robot.data.default_joint_pos[0].tolist(),target=(action[0]*term._scale+term._offset[0]).tolist())
      trace.append(row)
     obs,reward,done,info=wrapped.step(action)
     assert torch.isfinite(reward).all()
     rewards=env.reward_manager._step_reward[ids].sum(0)*env.step_dt
     reward_sum=rewards if reward_sum is None else reward_sum+rewards
     if (step+1)%200==0:print('PROGRESS',args.collision,label,step+1,'ended_loco',sum(i in ended for i in loco_ids),flush=True)
    active=False
    episodes=[ended[i] if i in ended else snapshot(i,True) for i in loco_ids]
    completed=[e for e in episodes if not e['censored']]
    peaks=[]
    if first_contact_peak is not None:
     for i,j in (first_contact_peak>10).nonzero().tolist():peaks.append(dict(a=sensor_paths[i].rsplit('/',1)[-1],b=robot.body_names[j],force_n=float(first_contact_peak[i,j])))
    summary=dict(completed=len(completed),censored=len(episodes)-len(completed),mean_observed_steps=statistics.mean(e['steps'] for e in episodes),mean_completed_steps=statistics.mean(e['steps'] for e in completed) if completed else None,
     tipped=sum(e['tipped'] for e in completed),fell_head=sum(e['fell_head'] for e in completed),fell_pelvis=sum(e['fell_pelvis'] for e in completed),timeouts=sum(e['timeout'] for e in completed),ends_before_push=sum(e['pushes']==0 for e in completed),
     samples=count,mean_abs_action=action_abs/count,style_score=style_sum/count,mean_task_per_step=float(reward_sum.sum()/count),rewards_per_step={k:float(v/count) for k,v in zip(env.reward_manager.active_terms,reward_sum)})
    cases[label]=dict(summary=summary,episodes=episodes,initial=initial,env0_initial_joint_pos=initial_q[0].tolist(),joint_names=robot.joint_names,env0_trace=trace,env0_contact_peaks=peaks,env0_contact_trace=contact_trace,
     policy_revision=checkpoint['environment_contract']['migration_revision'],weights_only_diagnostic=checkpoint is previous,original_contract=checkpoint['environment_contract'],diagnostic_contract=contract,push_disabled=disable_push,reset_joint_targets_held=hold_reset)
    assert all(torch.equal(v,saved[k]) for k,v in policy.state_dict().items())
    (D/f'{args.collision}.json').write_text(json.dumps(output,indent=2)+'\n')
    print('CASE',args.collision,label,json.dumps(summary),flush=True)
  output['status']='PASS';output['policy_parameters_unchanged']=True
  (D/f'{args.collision}.json').write_text(json.dumps(output,indent=2)+'\n');print('REPLAY_PASS',args.collision,flush=True)
 finally:env.close()
try:main()
finally:app.close(wait_for_replicator=False)
