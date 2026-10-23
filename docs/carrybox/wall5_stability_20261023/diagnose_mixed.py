"""Frozen discriminator, paired terminal windows, equal initial states; no training."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
from pathlib import Path
import json
import torch
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task,carrybox_walled as common,carrybox_physhsi as phy
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic,Wall5AMP
D=Path(__file__).resolve().parent;S=json.loads((D/'before.json').read_text());N=64

def main():
 torch.set_num_threads(2)
 ck=torch.load(S['checkpoint'],map_location=args.device,weights_only=False);old=torch.load(S['baseline_checkpoint'],map_location=args.device,weights_only=False)
 phy.fixed_hybrid=lambda ids,n,r,p:(torch.zeros_like(ids),torch.arange(len(ids),device=ids.device)%2==0)
 cfg,agent=CarryBoxWalled5EnvCfg(),CarryBoxWalled5PPORunnerCfg();cfg.scene.num_envs=N;cfg.seed=42;cfg.sim.device=args.device
 for k in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,k,262144)
 env=task.Wall5CarryBoxEnv(cfg=cfg)
 try:
  w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=w.reset()
  pc=agent.policy.to_dict();pc.pop('class_name');policy=CarryBoxWall5ActorCritic(obs,agent.obs_groups,29,**pc).to(args.device).eval()
  amp=Wall5AMP(600).to(args.device).eval();amp.load_state_dict(ck['amp']['model'],strict=True);amp_before={k:v.clone() for k,v in amp.state_dict().items()}
  coef=ck['amp']['config']['coef'];scale=ck['amp']['config']['reward_scale'];assert coef==.25 and scale==.5
  robot=env.scene['robot'];env.set_training_iteration(0);initial=None;runs={}
  with torch.inference_mode():
   for mode,weights in [('current',ck),('rev22',old)]:
    policy.load_state_dict(weights['model_state_dict'],strict=True);torch.manual_seed(73);obs,_=w.reset();env.episode_length_buf.zero_()
    states={k:v.clone() for k,v in dict(root=robot.data.root_state_w,q=robot.data.joint_pos,qd=robot.data.joint_vel,box=env.scene['box'].data.root_state_w).items()}
    if initial is None:initial=states
    else:
     for k,v in states.items():torch.testing.assert_close(v,initial[k],atol=2e-5,rtol=1e-5)
    for k,v in states.items():torch.testing.assert_close(v,torch.tensor(json.loads((D/'diagnosis.json').read_text())['initial_state'][k],device=v.device),atol=2e-5,rtol=1e-5)
    finished=torch.zeros(N,device=env.device,dtype=torch.bool);lengths=torch.full((N,),1000,device=env.device,dtype=torch.long);rows=[]
    for step in range(1000):
     live=~finished;obs,reward,done,extra=w.step(policy.act_inference(obs))
     motion=obs['amp'].clone();terminal=extra.get('terminal_observations')
     if done.any():
      ids=terminal['env_ids'];assert torch.equal(ids.sort().values,done.bool().nonzero().flatten())
      motion[ids]=terminal['obs']['amp']
     style=amp.predict_reward(motion);mixed=(1-coef)*reward+coef*scale*style
     alive=(~env.termination_manager.terminated).float()
     torch.testing.assert_close(env.reward_manager._step_reward.sum(-1)*env.step_dt,reward,atol=2e-6,rtol=1e-5)
     assert torch.isfinite(mixed).all()
     lengths[done.bool()&live]=step+1;finished|=done.bool()
     rows.append(dict(step=step+1,ids=live.nonzero().flatten().tolist(),task=reward[live].tolist(),style=style[live].tolist(),mixed=mixed[live].tolist(),alive=alive[live].tolist()))
     if finished.all():break
    runs[mode]=dict(lengths=lengths.tolist(),rows=rows)
    (D/'mixed_partial.json').write_text(json.dumps(runs)+'\n');print('MIXED_MODE',mode,'mean_steps',float(lengths.float().mean()),flush=True)
  assert all(torch.equal(v,amp_before[k]) for k,v in amp.state_dict().items())
  summaries={};prefix=torch.tensor(runs['current']['lengths'])
  for name,r in runs.items():
   ret=torch.zeros(64,dtype=torch.float64);new=ret.clone();common=ret.clone();style_sum=0;count=0
   for row in r['rows']:
    ids=torch.tensor(row['ids']);mixed=torch.tensor(row['mixed'],dtype=torch.float64);alive=torch.tensor(row['alive'],dtype=torch.float64);discount=.99**(row['step']-1)
    ret[ids]+=mixed*discount;new[ids]+=(mixed+.75*.02*alive)*discount
    shared=prefix[ids]>=row['step'];common[ids[shared]]+=mixed[shared]*discount
    style_sum+=sum(row['style']);count+=len(ids)
   summaries[name]=dict(mean_mixed_discounted_return=float(ret.mean()),mean_common_prefix_mixed_return=float(common.mean()),
    mean_style=style_sum/count,counterfactual_alive_weight1_return=float(new.mean()),mean_first_episode_seconds=sum(r['lengths'])/64*.02)
  result=dict(status='PASS',frozen_amp_checkpoint=S['checkpoint'],task_coef=1-coef,style_coef=coef*scale,summary=summaries,runs=runs,
    candidate='counterfactual addition of per-second weight1 is_alive, no actor change, no learning claim')
  (D/'mixed_diagnosis.json').write_text(json.dumps(result)+'\n');print('MIXED_DIAGNOSIS_PASS',json.dumps(summaries),flush=True)
 finally:env.close()
try:main()
except BaseException:
 import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
