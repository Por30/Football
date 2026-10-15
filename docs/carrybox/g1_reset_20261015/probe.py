import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import json, torch, gymnasium as gym
from pathlib import Path
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import euler_xyz_from_quat,wrap_to_pi,quat_apply_inverse
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg,CarryBoxWalled4PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner
OUT=Path(__file__).resolve().parent
cfg=CarryBoxWalled4EnvCfg();cfg.scene.num_envs=16;cfg.sim.device=args.device;cfg.seed=42
agent=CarryBoxWalled4PPORunnerCfg();env=gym.make('Template-Perceptual-Ball-CarryBox-Walled4-v0',cfg=cfg);b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
try:
 torch.set_num_threads(2)
 r=CarryBoxOnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device)
 r.warm_start('logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_21-08-12_wall4_handoff_v6_amp15_20261014_210808/model_14000.pt');policy=r.get_inference_policy(device=args.device)
 rob=b.scene['robot'];s=task.state(b);orig=b._reset_idx;active=None;hold=torch.zeros((16,29),device=b.device);report={}
 def snapshot(i):
  roll,pitch,yaw=euler_xyz_from_quat(rob.data.root_quat_w[i:i+1]);return dict(skill=int(s.skills[i]),steps=int(s.actual_episode_steps[i]),root_z=float(rob.data.root_pos_w[i,2]-b.scene.env_origins[i,2]),head_z=float(task.head_height(b)[i]),roll=float(wrap_to_pi(roll)[0]),pitch=float(wrap_to_pi(pitch)[0]),root_vel=rob.data.root_vel_w[i].tolist(),fell=bool(task.fallen(b)[i]),tipped=bool(task.tipped(b)[i]),timeout=bool(b.termination_manager.time_outs[i]))
 def reset(ids):
  if active is not None and getattr(b,'_carrybox_in_step',False):active['ends'].extend(snapshot(i) for i in ids.tolist())
  orig(ids);hold[ids]=(rob.data.joint_pos[ids]-rob.data.default_joint_pos[ids])/.25
  if active is not None and active.get('zero_velocity',False):
   rob.write_root_velocity_to_sim(torch.zeros((len(ids),6),device=b.device),env_ids=ids)
   rob.write_joint_velocity_to_sim(torch.zeros_like(rob.data.joint_vel[ids]),joint_ids=None,env_ids=ids)
 b._reset_idx=reset
 with torch.inference_mode():
  for name,ref,mode,zero in [('old_policy_loco',True,'policy',False),('hold_rsi_loco',True,'hold',False),('hold_rsi_zero_velocity',True,'hold',True),('default_stand',False,'zero',True)]:
   active=None;cfg.reference_init=ref;cfg.reset_skill_probabilities=(1.,0.,0.);torch.manual_seed(42);obs,_=w.reset()
   active=dict(ends=[],initial=[snapshot(i) for i in range(16)],frames=[],zero_velocity=zero)
   if zero:
    ids=torch.arange(16,device=b.device);reset(ids);obs=w.get_observations()
   for step in range(300):
    action=policy(obs) if mode=='policy' else hold.clone() if mode=='hold' else torch.zeros_like(hold)
    if step<8:active['frames'].append(dict(step=step,states=[snapshot(i) for i in range(4)],actions=action[:4].tolist()))
    obs,_,_,_=w.step(action)
   active['survivors']=[snapshot(i) for i in range(16)];report[name]=active
   print(name,'ends',len(active['ends']),'first',active['ends'][:2],flush=True)
 (OUT/'probe.json').write_text(json.dumps(report,indent=2));print('PROBE_DONE',flush=True)
finally:env.close();app.close(wait_for_replicator=False)
