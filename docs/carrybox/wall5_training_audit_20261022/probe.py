"""Read-only fixed-checkpoint audit: AMP/FK/history and reward/control scales."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
from pathlib import Path
import json,hashlib,statistics
import torch
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import quat_apply
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task,carrybox_walled as common
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic,Wall5AMP
from perceptual_ball.carrybox_wall5 import Wall5MotionLibrary
from perceptual_ball.carrybox_amp import joint_mapping
D=Path(__file__).resolve().parent;R=D.parents[2];S=json.loads((D/'selection.json').read_text());N=64

def stats(x):
 x=x.float().flatten();return dict(n=len(x),mean=float(x.mean()),median=float(x.median()),p95=float(torch.quantile(x,.95)),min=float(x.min()),max=float(x.max()))

def main():
 torch.set_num_threads(2);cfg,agent=CarryBoxWalled5EnvCfg(),CarryBoxWalled5PPORunnerCfg()
 cfg.scene.num_envs=N;cfg.seed=42;cfg.sim.device=args.device
 for key in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,key,262144)
 env=task.Wall5CarryBoxEnv(cfg=cfg)
 try:
  ck=torch.load(S['checkpoint'],map_location=args.device,weights_only=False);assert env.checkpoint_contract()==ck['environment_contract']
  w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=w.reset()
  pc=agent.policy.to_dict();pc.pop('class_name');policy=CarryBoxWall5ActorCritic(obs,agent.obs_groups,29,**pc).to(args.device)
  policy.load_state_dict(ck['model_state_dict'],strict=True);policy.eval()
  disc=Wall5AMP(600).to(args.device);disc.load_state_dict(ck['amp']['model'],strict=True);disc.eval()
  policy_saved={k:v.clone() for k,v in policy.state_dict().items()};disc_saved={k:v.clone() for k,v in disc.state_dict().items()}
  library=Wall5MotionLibrary(device=args.device,env_fps=50.)
  assert library.metadata==ck['amp']['dataset']
  env.set_training_iteration(0);env.set_training_iteration(int(ck['iter']))
  s=common.state(env);robot=env.scene['robot'];term=env.action_manager.get_term('joint_pos')
  inverse=torch.argsort(torch.tensor(joint_mapping(robot.joint_names),device=args.device))
  with torch.inference_mode():
   fk=[]
   for batch in range(4):
    # Write unperturbed reference poses and velocities; compare actual FK and
    # 60D simulation features with the expert loader at the identical native time.
    ids=torch.arange(N,device=env.device)%library.num_clips
    starts=torch.floor(torch.rand(N,device=env.device)*(library.lengths[ids]-12))
    expert=library.windows(ids,starts).reshape(N,10,60)[:,0]
    root=robot.data.root_state_w.clone();root[:,:3]=env.scene.env_origins;root[:,2]+=2.;qpos=torch.empty(N,29,device=env.device)
    box=env.scene['box'].data.root_state_w.clone();box[:,3:7]=box.new_tensor([1.,0.,0.,0.]);box[:,7:]=0
    for clip in ids.unique().tolist():
     mask=ids==clip;t=starts[mask].long();joint,_,quat,angular=library.clips[clip]
     ends,linear,offset=library.task_clips[clip]
     root[mask,3:7]=quat[t];root[mask,7:10]=linear[t];root[mask,10:]=quat_apply(quat[t],angular[t])
     qpos[mask]=joint[t][:,inverse];box[mask,:3]=root[mask,:3]+offset[t]
    robot.write_root_link_state_to_sim(root);robot.write_joint_state_to_sim(qpos,torch.zeros_like(qpos));env.scene['box'].write_root_state_to_sim(box);env.sim.forward()
    actual=task.amp_frame(env);delta=(actual-expert).abs()
    fk.append(dict(clip_ids=ids.tolist(),starts=starts.tolist(),error=delta.tolist(),actual=actual.tolist(),expert=expert.tolist()))
   # Same expert window, only the artificial repeated-reset prefix differs.
   expert,clip_ids=library.sample_expert_amp_obs(2048,return_clip_ids=True);x=expert.reshape(-1,10,60)
   padding={}
   for age in (0,1,3,5,8,9):
    altered=x.clone();altered[:,:10-age]=x[:,9-age:10-age]
    padding[str(age)]={'style':stats(disc.predict_reward(altered.flatten(1))), 'logit':stats(disc(altered.flatten(1)))}
   expert_style=disc.predict_reward(expert);expert_group={g:stats(expert_style[torch.tensor([library.clip_groups[i]==g for i in clip_ids.tolist()],device=env.device)]) for g in set(library.clip_groups)}
   kp=robot.data.joint_stiffness.clone();assert torch.isfinite(kp).all() and (kp>0).all()
   runs={}
   for mode in ('sample','mean','reset_target'):
    torch.manual_seed(42);obs,_=w.reset();env.episode_length_buf.zero_()
    hold=((robot.data.joint_pos[:,term._joint_ids]-term._offset)/term._scale).clone()
    first_kind=torch.where(s.default_reset,0,s.skills+1).clone();first_steps=torch.zeros(N,device=env.device,dtype=torch.long)
    first_done=torch.zeros(N,device=env.device,dtype=torch.bool);data=[]
    # Hold each newly reset pose if the baseline runs into later episodes.
    for step in range(256):
     kind=torch.where(s.default_reset,0,s.skills+1).clone();age=s.actual_episode_steps.clone()+1
     mean=policy.act_inference(obs)
     action=policy.act(obs) if mode=='sample' else mean
     if mode=='reset_target':action=hold;mean=hold
     obs,reward,done,extra=w.step(action)
     assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
     motion=obs['amp'].clone();terminal=extra.get('terminal_observations')
     if terminal is not None:motion[terminal['env_ids']]=terminal['obs']['amp']
     style=disc.predict_reward(motion);names=env.reward_manager.active_terms
     rewards=env.reward_manager._step_reward*env.step_dt
     torch.testing.assert_close(rewards.sum(-1),reward,atol=1e-6,rtol=1e-5)
     tau=robot.data.applied_torque;raw=-1e-4*env.step_dt*tau.square().sum(-1)
     normalized=-1e-4*env.step_dt*(tau/kp).square().sum(-1)
     # Robot state is post-reset for done rows; cached reward terms and motion
     # are pre-reset. Torque estimates are retained by this IsaacLab reset.
     difference=(raw-rewards[:,names.index('torques')]).abs()
     assert float(difference.max())<1e-5,float(difference.max())
     bounds=task.action_bounds(env);low,high=bounds.chunk(2,-1)
     first_new=(~first_done)&done.bool();first_steps[first_new]=step+1;first_done|=done.bool()
     data.append(torch.stack((kind.float(),age.float(),done.float(),reward,style,.75*reward+.125*style,
      rewards[:,names.index('walk_task')],rewards[:,names.index('carryup_task')],raw,normalized,
      rewards[:,names.index('action_rate')],(mean-low).clamp_max(0).abs().add((mean-high).clamp_min(0)).amax(-1),
      term.target_saturation.float().mean(-1)),dim=-1).cpu())
     if mode=='reset_target' and done.any():
      ids=done.nonzero().flatten();hold[ids]=(robot.data.joint_pos[ids][:,term._joint_ids]-term._offset[ids])/term._scale
    first_steps[~first_done]=256
    all_data=torch.cat(data);columns=['kind','age','done','task','style','mixed','walk','carryup','torque_raw','torque_normalized','action_rate','mean_bound_excess','clipped_fraction']
    groups={}
    for k,name in enumerate(('default','loco','pickup','hold')):
     mask=all_data[:,0]==k;d=all_data[mask];first=first_steps[first_kind==k]
     groups[name]={'transitions':len(d),'first_episode_steps':stats(first),'first_censored':int((~first_done[first_kind==k]).sum()),'short_window_fraction':float((d[:,1]<9).float().mean()),'means':dict(zip(columns[3:],d[:,3:].mean(0).tolist()))}
    age_scores={str(a):stats(all_data[(all_data[:,1]==a),4]) for a in (1,2,3,5,8,9,12,20) if (all_data[:,1]==a).any()}
    runs[mode]=dict(groups=groups,age_style=age_scores,columns=columns,raw=all_data.tolist())
    print('CASE',mode,{k:v['first_episode_steps']['mean'] for k,v in groups.items()},flush=True)
    (D/'probe_partial.json').write_text(json.dumps(dict(fk=fk,padding=padding,expert_group=expert_group,runs=runs))+'\n')
  assert all(torch.equal(v,policy_saved[k]) for k,v in policy.state_dict().items())
  assert all(torch.equal(v,disc_saved[k]) for k,v in disc.state_dict().items())
  result=dict(status='PASS',checkpoint=S['checkpoint'],iteration=int(ck['iter']),num_envs=N,steps_per_mode=256,policy_dt=.02,fk=fk,padding=padding,expert_group=expert_group,runs=runs,weights_unchanged=True,stiffness=kp[0].tolist(),joint_names=robot.joint_names,amp_normalizer_std=disc.obs_std[:60].tolist())
  (D/'probe.json').write_text(json.dumps(result)+'\n');print('TRAINING_AUDIT_PASS',flush=True)
 finally:env.close()
try:main()
except BaseException:
 import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
