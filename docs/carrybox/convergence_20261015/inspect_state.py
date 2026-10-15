"""Supplementary 200-step inference probe, no optimization or production mutation."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import torch,gymnasium as gym,json
from pathlib import Path
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import quat_apply_inverse,euler_xyz_from_quat,wrap_to_pi
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg,CarryBoxWalled4PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task,carrybox as base
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner
from perceptual_ball.carrybox_amp import joint_mapping
out=Path(__file__).resolve().parent;root=out.parents[2]
def main():
 torch.set_num_threads(2);cfg=CarryBoxWalled4EnvCfg();cfg.scene.num_envs=16;cfg.seed=42;cfg.sim.device=args.device
 env=gym.make('Template-Perceptual-Ball-CarryBox-Walled4-v0',cfg=cfg)
 try:
  b=env.unwrapped;agent=CarryBoxWalled4PPORunnerCfg();w=RslRlVecEnvWrapper(env,clip_actions=9)
  runner=CarryBoxOnPolicyRunner(w,agent.to_dict(),log_dir=None,device=b.device)
  c=torch.load(root/'logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_21-08-12_wall4_handoff_v6_amp15_20261014_210808/model_13600.pt',map_location=b.device,weights_only=False)
  runner.alg.policy.load_state_dict(c['model_state_dict']);runner.alg.policy.eval();runner.alg.amp.load_state_dict(c['amp']['model']);runner.alg.amp.eval()
  robot=b.scene['robot'];box=b.scene['box'];s=task.state(b);lim=robot.data.soft_joint_pos_limits[0];mapping=joint_mapping(robot.joint_names);costs={}
  for name,(q,*_) in zip(s.library.clip_names,s.library.clips):
   soft=lim[mapping];cost=5*((soft[:,0]-q).clamp_min(0)+(q-soft[:,1]).clamp_min(0)).sum(-1)
   costs[name]={'mean':float(cost.mean()),'max':float(cost.max())}
  obs,_=w.reset();rows=[];transitions=[];joint_saturation=torch.zeros(29,device=b.device);errors=torch.zeros(29,device=b.device);count=0
  with torch.inference_mode():
   for step in range(200):
    action=runner.alg.policy.act_inference(obs)
    bottom,upright,speed=base.lift_geometry(b);contact=base.hand_contacts(b).all(-1)
    gravity=quat_apply_inverse(robot.data.body_quat_w[:,s.torso],robot.data.GRAVITY_VEC_W)
    roll,pitch,_=euler_xyz_from_quat(robot.data.root_quat_w)
    if step%10==0:
     for i in range(16):rows.append(dict(step=step,skill=int(s.skills[i]),age=int(b.episode_length_buf[i]),root_z=float(robot.data.root_pos_w[i,2]-b.scene.env_origins[i,2]),root_roll=float(wrap_to_pi(roll[i])),root_pitch=float(wrap_to_pi(pitch[i])),head_z=float(robot.data.body_pos_w[i,s.head,2]-b.scene.env_origins[i,2]),box_z=float(box.data.root_pos_w[i,2]-b.scene.env_origins[i,2]),bottom=float(bottom[i]),upright=float(upright[i]),speed=float(speed[i]),both=bool(contact[i]),torso_gravity_xy=float(gravity[i,:2].norm()),hold_count=int(b._carrybox_hold.count[i]),max_abs_action=float(action[i].abs().max())))
    joint_saturation+=(action.abs()>9).float().sum(0);count+=16
    errors+=(action.clamp(-9,9)*.25+robot.data.default_joint_pos-robot.data.joint_pos).abs().sum(0)
    skills_before=s.skills.clone();age_before=b.episode_length_buf.clone()
    obs,reward,done,info=w.step(action)
    for i in range(16):transitions.append(dict(skill=int(skills_before[i]),age=int(age_before[i]),reward=float(reward[i]),done=bool(done[i]),terms={name:float(b.reward_manager._step_reward[i,j]*b.step_dt) for j,name in enumerate(b.reward_manager.active_terms)}))
    assert torch.isfinite(reward).all()
  result=dict(status='PASS',policy_steps=200,training_updates=0,actual_soft_limits={name:lim[i].cpu().tolist() for i,name in enumerate(robot.joint_names)},actual_reference_penalty=costs,saturation_fraction={name:float(joint_saturation[i]/count) for i,name in enumerate(robot.joint_names)},mean_abs_target_error={name:float(errors[i]/count) for i,name in enumerate(robot.joint_names)},samples=rows,transitions=transitions)
  (out/'state_probe.json').write_text(json.dumps(result,indent=2)+'\n');print('STATE_PROBE_PASS')
 finally:env.close()
try:main()
finally:app.close(wait_for_replicator=False)
