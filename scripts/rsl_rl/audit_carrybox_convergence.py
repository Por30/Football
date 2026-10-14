"""Bounded inference-only diagnosis; never resumes or updates a trained policy."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import json,copy
from pathlib import Path
import numpy as np
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import euler_xyz_from_quat,wrap_to_pi
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg,CarryBoxWalled4PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
from perceptual_ball.carrybox_amp import SOURCE_JOINT_NAMES,joint_mapping
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/carrybox/convergence_20261014';OUT.mkdir(parents=True,exist_ok=True)
RUN=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_00-52-12_wall4_afterfootball_20261013'

def main():
 torch.set_num_threads(2)
 cfg=CarryBoxWalled4EnvCfg();cfg.scene.num_envs=16;cfg.seed=42;cfg.sim.device=args.device
 agent=CarryBoxWalled4PPORunnerCfg()
 env=gym.make('Template-Perceptual-Ball-CarryBox-Walled4-v0',cfg=cfg)
 try:
  b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
  runner=CarryBoxOnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device)
  robot=b.scene['robot'];mapping=joint_mapping(robot.joint_names)
  defaults=robot.data.default_joint_pos[0,mapping].cpu()
  coverage={}
  for path in sorted((ROOT/'findbox').glob('*/*.pt')):
   data=torch.load(path,map_location='cpu',weights_only=True)
   if not isinstance(data,dict) or 'joint_position' not in data:continue
   actions=(data['joint_position'].float()-defaults)/.25
   bad=actions.abs()>5.
   coverage[str(path.relative_to(ROOT/'findbox'))]=dict(frames=len(actions),unreachable_frame_fraction=float(bad.any(-1).float().mean()),max_required_abs_action=float(actions.abs().max()),joints=[SOURCE_JOINT_NAMES[i] for i in bad.any(0).nonzero().flatten().tolist()])
  (OUT/'reference_action_coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
  original_reset=b._reset_idx
  active=None
  ages=torch.zeros(b.num_envs,device=b.device,dtype=torch.long)
  holding=torch.zeros(b.num_envs,29,device=b.device)
  def reset_capture(ids):
   if active is not None and getattr(b,'_carrybox_in_step',False):
    roll,pitch,_=euler_xyz_from_quat(robot.data.root_quat_w[ids]);roll=wrap_to_pi(roll);pitch=wrap_to_pi(pitch)
    for j,i in enumerate(ids.tolist()):
     active['episodes'].append(dict(skill=int(task.state(b).skills[i]),steps=int(b.episode_length_buf[i]),roll=float(roll[j]),pitch=float(pitch[j]),fell=bool(task.fallen(b)[i]),tipped=bool(task.tipped(b)[i])))
   original_reset(ids)
   holding[ids]=(robot.data.joint_pos[ids]-robot.data.default_joint_pos[ids])/.25
  b._reset_idx=reset_capture
  cases={}
  checkpoints=[('default_target',None),('hold_reset_pose',None),('checkpoint_0',RUN/'model_0.pt'),('checkpoint_200',RUN/'model_200.pt'),('checkpoint_14600',RUN/'model_14600.pt')]
  with torch.inference_mode():
   for name,path in checkpoints:
    active=None;torch.manual_seed(42)
    obs,_=w.reset();ages.zero_()
    holding.copy_((robot.data.joint_pos-robot.data.default_joint_pos)/.25)
    if path:
     # Explicit read-only policy replay across reward contract revisions, not resume.
     ckpt=torch.load(path,map_location=args.device,weights_only=False)
     runner.alg.policy.load_state_dict(ckpt['model_state_dict']);runner.alg.policy.eval()
    active=dict(episodes=[])
    alive=leaked=valid=total=0;saturated=0.;raw_max=0.;fixed_penalty=old_penalty=0.
    for step in range(240):
     if name=='default_target':action=torch.zeros_like(holding)
     elif name=='hold_reset_pose':action=holding.clone()
     else:action=runner.alg.policy.act_inference(obs)
     saturated+=float((action.abs()>5).float().sum());raw_max=max(raw_max,float(action.abs().max()))
     obs,reward,done,info=w.step(action)
     manager=b.termination_manager
     history=(manager.get_term('fell')|manager.get_term('tipped')) & ~manager.time_outs
     fixed=task.failure_event(b).bool()
     now=manager.terminated & ~manager.time_outs
     assert not (fixed & ~now).any()
     actual=b.reward_manager._step_reward[:,b.reward_manager.active_terms.index('fall')]*b.step_dt
     torch.testing.assert_close(actual,-.2*fixed.float())
     alive+=int((~done.bool()).sum());leaked+=int((history & ~done.bool()).sum())
     fixed_penalty+=float(actual.sum());old_penalty+=float((-.2*history.float()).sum())
     ages+=1;valid+=int((ages>=9).sum());total+=b.num_envs;ages[done.bool()]=0
     assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
    episodes=active['episodes'];summaries={}
    for skill in range(3):
     e=[v for v in episodes if v['skill']==skill]
     summaries[str(skill)]=dict(completed_episodes=len(e),mean_steps=float(np.mean([v['steps'] for v in e])) if e else None,
       tipped_fraction=float(np.mean([v['tipped'] for v in e])) if e else None)
    cases[name]=dict(transitions=total,completed_episodes=len(episodes),mean_episode_steps=float(np.mean([v['steps'] for v in episodes])),
      amp_valid_fraction=valid/total,alive_transitions=alive,old_false_penalty_alive_transitions=leaked,
      fixed_false_penalty_alive_transitions=0,old_fall_penalty_sum=old_penalty,fixed_fall_penalty_sum=fixed_penalty,
      raw_action_max=raw_max,clipped_action_fraction=saturated/(total*29),by_skill=summaries,terminal_examples=episodes[:12])
    print('AUDIT_CASE',name,json.dumps({k:v for k,v in cases[name].items() if k!='terminal_examples'}),flush=True)
    assert leaked>0,'Need a real post-reset alive transition to exercise the original bug'
   active=None
  report=dict(status='PASS',training_updates=0,num_envs=b.num_envs,policy_dt=b.step_dt,cases=cases,environment_contract=b.checkpoint_contract())
  (OUT/'rollout_audit.json').write_text(json.dumps(report,indent=2)+'\n')
  print('CARRYBOX_CONVERGENCE_AUDIT_PASS',flush=True)
 finally:env.close()
try:main()
except BaseException:
 import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
