"""Bounded inference-only wall4 failure diagnosis; production training untouched."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import json,statistics
from pathlib import Path
import torch,gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import euler_xyz_from_quat,wrap_to_pi
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg,CarryBoxWalled4PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task,carrybox as base
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_x2_rewards import reward_terms
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
RUN=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_21-08-12_wall4_handoff_v6_amp15_20261014_210808'
def summary(values):
 return dict(n=len(values),mean=statistics.mean(values),min=min(values),max=max(values)) if values else dict(n=0)
def main():
 torch.set_num_threads(2)
 cfg=CarryBoxWalled4EnvCfg();cfg.scene.num_envs=16;cfg.seed=42;cfg.sim.device=args.device
 agent=CarryBoxWalled4PPORunnerCfg();env=gym.make('Template-Perceptual-Ball-CarryBox-Walled4-v0',cfg=cfg)
 try:
  b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
  runner=CarryBoxOnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device)
  robot=b.scene['robot'];box=b.scene['box'];s=task.state(b);original_reset=b._reset_idx;active=None;hold=torch.zeros((16,29),device=b.device)
  def reset_capture(ids):
   if active is not None and getattr(b,'_carrybox_in_step',False):
    roll,pitch,_=euler_xyz_from_quat(robot.data.root_quat_w[ids]);roll=wrap_to_pi(roll);pitch=wrap_to_pi(pitch)
    for j,i in enumerate(ids.tolist()):
     active['episodes'].append(dict(skill=int(s.skills[i]),steps=int(b.episode_length_buf[i]),roll=float(roll[j]),pitch=float(pitch[j]),fell=bool(task.fallen(b)[i]),tipped=bool(task.tipped(b)[i]),success=bool(s.achieved[i]),box_z=float(box.data.root_pos_w[i,2]-b.scene.env_origins[i,2])))
   original_reset(ids);hold[ids]=(robot.data.joint_pos[ids]-robot.data.default_joint_pos[ids])/.25
   if active is not None:
    hands=robot.data.body_pos_w[:,s.hands].mean(1)
    for i in ids.tolist():active['resets'].append(dict(skill=int(s.skills[i]),root_z=float(robot.data.root_pos_w[i,2]-b.scene.env_origins[i,2]),box_z=float(box.data.root_pos_w[i,2]-b.scene.env_origins[i,2]),hand_error=float((hands[i]-box.data.root_pos_w[i]).norm())))
  b._reset_idx=reset_capture
  latest=torch.load(RUN/'model_13600.pt',map_location=b.device,weights_only=False)
  runner.alg.amp.load_state_dict(latest['amp']['model']);runner.alg.amp.eval()
  expert,clipids=s.library.sample_expert_amp_obs(2048,return_clip_ids=True)
  expert_report={}
  for label,values in [('expert',expert),('expert_plus_joint_noise_0.02',expert.clone()),('expert_plus_velocity_noise_0.2',expert.clone())]:
   if 'joint' in label: values.view(-1,10,64)[:,:,:29].add_(torch.randn_like(values.view(-1,10,64)[:,:,:29])*.02)
   if 'velocity' in label: values.view(-1,10,64)[:,:,29:58].add_(torch.randn_like(values.view(-1,10,64)[:,:,29:58])*.2)
   with torch.no_grad():scores=runner.alg.amp.predict_reward(values)
   expert_report[label]=dict(mean=float(scores.mean()),zero_fraction=float((scores==0).float().mean()))
  cases={}
  configurations=[('model0',0,False,False,False,500),('model3600',3600,False,False,False,500),('model13600',13600,False,False,False,500),('model13600_stochastic',13600,True,False,False,500),('model13600_no_push',13600,False,True,False,500),('hold_reset_pose',None,False,False,False,500),('model13600_pickup_RSI',13600,False,False,True,400)]
  interval_cfg=b.event_manager._mode_term_cfgs['interval'][0];original_push=interval_cfg.func
  with torch.inference_mode():
   for name,iteration,stochastic,no_push,pickup,steps in configurations:
    active=None;torch.manual_seed(42)
    b.cfg.reset_skill_probabilities=(0.,1.,0.) if pickup else (.8,0.,.2)
    interval_cfg.func=(lambda *a,**k:None) if no_push else original_push
    obs,_=w.reset();hold.copy_((robot.data.joint_pos-robot.data.default_joint_pos)/.25)
    if iteration is not None:
     c=torch.load(RUN/f'model_{iteration}.pt',map_location=b.device,weights_only=False);runner.alg.policy.load_state_dict(c['model_state_dict']);runner.alg.policy.eval()
    active=dict(episodes=[],resets=[]);stats=[];ages=torch.zeros(16,device=b.device,dtype=torch.long)
    for step in range(steps):
     action=hold.clone() if iteration is None else (runner.alg.policy.act(obs) if stochastic else runner.alg.policy.act_inference(obs))
     terms=reward_terms(b);contacts=base.hand_contacts(b);hands=robot.data.body_pos_w[:,s.hands].mean(1)
     limits=robot.data.soft_joint_pos_limits;target=action.clamp(-9,9)*.25+robot.data.default_joint_pos
     style=runner.alg.amp.predict_reward(obs['amp']);bottom,upright,speed=base.lift_geometry(b)
     for skill in range(3):
      mask=(s.skills==skill)&(ages>=9)
      if mask.any():
       near=(box.data.root_pos_w[:,:2]-robot.data.root_pos_w[:,:2]).norm(dim=-1)<.7
       stats.append(dict(skill=skill,n=int(mask.sum()),style=float(style[mask].sum()),near=float(near[mask].sum()),both=float(contacts[mask].all(-1).sum()),box_high=float((box.data.root_pos_w[mask,2]-b.scene.env_origins[mask,2]>.6).sum()),strict=float(s.achieved[mask].sum()),hand_error=float((hands-box.data.root_pos_w).norm(dim=-1)[mask].sum()),walk=float(terms['walk_task'][mask].sum()),carry=float(terms['carryup_task'][mask].sum()),stand=float(terms['standup_task'][mask].sum()),clip=float((action[mask].abs()>9).float().mean(-1).sum()),target_limit=float(((target<limits[:,:,0])|(target>limits[:,:,1]))[mask].float().mean(-1).sum())))
     obs,reward,done,info=w.step(action);ages+=1;ages[done.bool()]=0
     assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
    by_skill={}
    for skill in range(3):
     es=[e for e in active['episodes'] if e['skill']==skill];ss=[e for e in stats if e['skill']==skill];n=sum(e['n'] for e in ss)
     by_skill[str(skill)]=dict(completed=len(es),completed_length_steps=summary([e['steps'] for e in es]),tipped_fraction=statistics.mean([e['tipped'] for e in es]) if es else None,success_episodes=sum(e['success'] for e in es),valid_transitions=n,per_transition={k:sum(e[k] for e in ss)/n for k in ['style','near','both','box_high','strict','hand_error','walk','carry','stand','clip','target_limit']} if n else {})
    cases[name]=dict(steps=steps,by_skill=by_skill,unfinished_episode_ages=b.episode_length_buf.cpu().tolist(),episodes=active['episodes'],reset_samples=active['resets'][:80])
    print('CASE',name,json.dumps(by_skill),flush=True)
    (OUT/'replay_result.json').write_text(json.dumps(dict(status='RUNNING',num_envs=16,training_updates=0,expert_discriminator=expert_report,cases=cases),indent=2)+'\n')
   active=None
  result=dict(status='PASS',num_envs=16,training_updates=0,total_policy_steps=3400,expert_discriminator=expert_report,cases=cases)
  (OUT/'replay_result.json').write_text(json.dumps(result,indent=2)+'\n');print('WALL4_DIAGNOSIS_PASS',flush=True)
 finally:env.close()
try:main()
finally:app.close(wait_for_replicator=False)
