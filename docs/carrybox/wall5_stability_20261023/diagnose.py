"""Same initial states, bounded diagnostic overrides, frozen actor comparisons."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
from pathlib import Path
import json,hashlib
import torch
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import euler_xyz_from_quat,wrap_to_pi
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task,carrybox_walled as common,carrybox_physhsi as phy
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic
D=Path(__file__).resolve().parent;R=D.parents[2];S=json.loads((D/'before.json').read_text());N=64

def main():
 torch.set_num_threads(2)
 ck=torch.load(S['checkpoint'],map_location=args.device,weights_only=False)
 old=torch.load(S['baseline_checkpoint'],map_location=args.device,weights_only=False)
 # Diagnostic allocation only: same 32 defaults + 32 loco for each actor.
 def empty_only(count,device='cpu'):
  return torch.zeros(count,device=device,dtype=torch.long),torch.arange(count,device=device)%2==0
 phy.sample_hybrid=empty_only
 cfg,agent=CarryBoxWalled5EnvCfg(),CarryBoxWalled5PPORunnerCfg();cfg.scene.num_envs=N;cfg.seed=42;cfg.sim.device=args.device
 for k in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,k,262144)
 env=task.Wall5CarryBoxEnv(cfg=cfg)
 try:
  assert env.checkpoint_contract()==ck['environment_contract']
  w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=w.reset()
  pc=agent.policy.to_dict();pc.pop('class_name');policy=CarryBoxWall5ActorCritic(obs,agent.obs_groups,29,**pc).to(args.device);policy.eval()
  robot=env.scene['robot'];s=common.state(env);term=env.action_manager.get_term('joint_pos')
  env.set_training_iteration(0) # Same yaw=0 / push=0 for all diagnostic modes.
  runs={};reference_initial=None
  with torch.inference_mode():
   for mode in ('current','rev22','hold_reset_target','current_no_delay'):
    policy.load_state_dict(old['model_state_dict'] if mode=='rev22' else ck['model_state_dict'],strict=True)
    saved={k:v.clone() for k,v in policy.state_dict().items()}
    torch.manual_seed(73);obs,_=w.reset();env.episode_length_buf.zero_()
    initial=dict(root=robot.data.root_state_w.clone(),q=robot.data.joint_pos.clone(),qd=robot.data.joint_vel.clone(),box=env.scene['box'].data.root_state_w.clone())
    if reference_initial is None:reference_initial=initial
    else:
     for k,v in initial.items():torch.testing.assert_close(v,reference_initial[k],atol=2e-5,rtol=1e-5)
    initial_defaults=s.default_reset.clone();assert int(initial_defaults.sum())==32
    if mode=='current_no_delay':term.delay.index.fill_(4)
    hold=(robot.data.joint_pos[:,term._joint_ids]-term._offset)/term._scale
    finished=torch.zeros(N,device=env.device,dtype=torch.bool);length=torch.full((N,),1000,device=env.device,dtype=torch.long)
    causes={name:torch.zeros(N,device=env.device,dtype=torch.bool) for name in env.termination_manager.active_terms}
    trace=[];rewards=[]
    for step in range(1000):
     live=~finished;action=hold if mode=='hold_reset_target' else policy.act_inference(obs)
     pre_q=robot.data.joint_pos.clone();pre_root=robot.data.root_state_w.clone()
     obs,reward,done,extra=w.step(action)
     assert torch.isfinite(reward).all() and all(torch.isfinite(x).all() for x in obs.values())
     new=done.bool()&live;length[new]=step+1
     for name in causes:causes[name][new]=env.termination_manager.get_term(name)[new]
     finished|=done.bool()
     reward_parts=env.reward_manager._step_reward*env.step_dt
     rewards.append(dict(step=step+1,live_ids=live.nonzero().flatten().tolist(),values=reward_parts[live].tolist()))
     if step<40:
      trace.append(dict(step=step+1,ids=[0,1],live=live[:2].tolist(),root_before=pre_root[:2].tolist(),q_before=pre_q[:2].tolist(),actions=action[:2].tolist(),torque=robot.data.applied_torque[:2].tolist(),done=done[:2].tolist()))
     if finished.all():break
    groups={}
    for label,mask in [('default',initial_defaults),('loco',~initial_defaults)]:
     groups[label]=dict(n=int(mask.sum()),mean_steps=float(length[mask].float().mean()),min_steps=int(length[mask].min()),max_steps=int(length[mask].max()),
        censored=int((~finished[mask]).sum()),causes={k:int(v[mask].sum()) for k,v in causes.items()})
    assert all(torch.equal(v,saved[k]) for k,v in policy.state_dict().items())
    runs[mode]=dict(groups=groups,lengths=length.tolist(),initial_defaults=initial_defaults.tolist(),trace=trace,reward_names=env.reward_manager.active_terms,rewards=rewards)
    (D/'diagnosis_partial.json').write_text(json.dumps(runs)+'\n');print('MODE',mode,json.dumps(groups),flush=True)
  result=dict(status='PASS',checkpoint=S['checkpoint'],baseline_checkpoint=S['baseline_checkpoint'],
    diagnostic_overrides=['32 default and 32 loco RSI','yaw/push effective iteration0'],
    old_policy_transfer='strict parameter shapes only; old environment contract intentionally not resumed',
    old_contract_differences={k:dict(old=old['environment_contract'].get(k),current=ck['environment_contract'].get(k)) for k in old['environment_contract'].keys()|ck['environment_contract'].keys() if old['environment_contract'].get(k)!=ck['environment_contract'].get(k)},
    initial_state={k:v.tolist() for k,v in reference_initial.items()},runs=runs)
  (D/'diagnosis.json').write_text(json.dumps(result)+'\n');print('DIAGNOSIS_PASS',flush=True)
 finally:env.close()
try:main()
except BaseException:
 import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
