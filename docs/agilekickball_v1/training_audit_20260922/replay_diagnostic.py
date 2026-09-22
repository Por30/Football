"""Read-only equal-condition policy replay; no gradients or course advancement."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
env=None
import json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v1_env_cfg import AgileKickballV1EnvCfg,AgileKickballV1PPORunnerCfg
from perceptual_ball.rsl_rl_extensions.modules import PerceptionActorCritic

def main():
 global env
 torch.set_num_threads(2);out=Path('docs/agilekickball_v1/training_audit_20260922')
 cfg=AgileKickballV1EnvCfg();cfg.scene.num_envs=16;cfg.sim.device=args.device;cfg.seed=922
 env=gym.make('Template-Perceptual-Ball-AgileKickball-v1',cfg=cfg);base=env.unwrapped;wrapped=RslRlVecEnvWrapper(env)
 obs,_=wrapped.reset();agent=AgileKickballV1PPORunnerCfg();pc=agent.policy.to_dict();pc.pop('class_name')
 policy=PerceptionActorCritic(obs,agent.obs_groups,29,**pc).to(args.device).eval();kb=base._kickball;robot=base.scene['robot']
 paths={'v1':'logs/rsl_rl/agilekickball_v1/2026-09-21_12-52-45_success_curriculum_scratch/model_30600.pt','v0':'logs/rsl_rl/agilekickball_v0/2026-09-20_18-02-42_learning_fix/model_25200.pt'}
 result={}
 with torch.inference_mode():
  for version,stochastic in [('v1',False),('v1',True),('v0',False)]:
   ckpt=torch.load(paths[version],map_location=args.device,weights_only=False);policy.load_state_dict(ckpt['model_state_dict']);policy.eval()
   torch.manual_seed(922);kb.load_curriculum_state_dict(None);kb.curriculum_training=False;obs,_=wrapped.reset()
   before=kb.metrics();steps=1000;dones=0;waiting=0;gates={};height=[];joint=[];stablemax=0.;candidates=0;proxy=0;returned=0
   q=robot.data
   for step in range(steps):
    wait=~kb.ball_active;waiting+=int(wait.sum())
    if wait.any():
     z=q.root_pos_w[:,2]-base.scene.env_origins[:,2]
     fz=q.body_link_pos_w[:,kb.foot_body_ids,2]-base.scene.env_origins[:,2,None]
     j=q.joint_vel.square().mean(-1).sqrt()
     conditions={'upright_xy':q.projected_gravity_b[:,:2].norm(dim=-1)<.15,'upright_z':q.projected_gravity_b[:,2]<-.98,'root_speed':q.root_lin_vel_w.norm(dim=-1)<.25,'angular_speed':q.root_ang_vel_b.norm(dim=-1)<.5,'height':(z>.7)&(z<.9),'joint_speed':j<1.5,'feet_height':(fz<.12).all(-1)&(fz>-.03).all(-1),'all':kb.balanced()}
     for k,v in conditions.items():gates[k]=gates.get(k,0)+int((v&wait).sum())
     height.append(z[wait].clone());joint.append(j[wait].clone());stablemax=max(stablemax,kb.stable_elapsed.max().item())
    old_candidate=kb.candidate.clone();old_returned=kb.returned.clone()
    action=policy.act(obs) if stochastic else policy.act_inference(obs)
    obs,_,done,_=wrapped.step(action);dones+=int(done.sum())
    proxy+=int(kb.kick_success_flag.sum());candidates+=int((kb.candidate&~old_candidate).sum());returned+=int((kb.returned&~old_returned).sum())
   after=kb.metrics();delta={k:after[k]-before[k] for k in ['AgileKickball/serves','AgileKickball/recovered_serves','AgileV1/settled_rounds','AgileV1/curriculum_proxy_successes']}
   record={'checkpoint':paths[version],'stochastic':stochastic,'num_envs':16,'steps':steps,'speed_range':kb.serve_speed_range,'distance_range':kb.serve_distance_range,'episode_terminations':dones,'delta_counters_excluding_initial16':delta,'raw_kick_proxy_pulses':proxy,'candidate_rising_edges':candidates,'return_progress_rising_edges':returned,'waiting_samples':waiting,'waiting_gate_pass_fraction':{k:v/max(1,waiting) for k,v in gates.items()},'max_stable_interval_s':stablemax,'waiting_mean_height':torch.cat(height).mean().item() if height else None,'waiting_mean_joint_velocity_rms':torch.cat(joint).mean().item() if joint else None}
   result[f'{version}_{"stochastic" if stochastic else "deterministic"}']=record;print(json.dumps(record),flush=True)
 (out/'replay.json').write_text(json.dumps(result,indent=2)+'\n')
try:main()
except BaseException:
 import traceback,sys,os
 traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
finally:
 if env is not None:env.close()
 app.close(wait_for_replicator=False)
