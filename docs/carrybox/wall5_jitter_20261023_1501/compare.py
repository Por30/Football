"""Frozen-policy replay: one diagnostic override per process."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['no_self','no_delay'],required=True)
AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import json,hashlib
from pathlib import Path
import torch
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic
from perceptual_ball.tasks.manager_based.perceptual_ball import carrybox_wall5_env_cfg as config
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task,carrybox_walled as common
from trace import JitterTrace
D=Path(__file__).resolve().parent;R=D.parents[2];S=json.loads((D/'selection.json').read_text())

def main():
 torch.set_num_threads(2)
 for name,h in S['source_sha256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h,name
 ck=torch.load(S['checkpoint'],map_location=args.device,weights_only=False)
 assert hashlib.sha256(Path(S['checkpoint']).read_bytes()).hexdigest()==S['checkpoint_sha256']
 cfg,agent=config.CarryBoxWalled5EnvCfg(),config.CarryBoxWalled5PPORunnerCfg()
 cfg.scene.num_envs=4;cfg.seed=42;cfg.sim.device=args.device
 if args.mode=='no_self':cfg.scene.robot.spawn.articulation_props.enabled_self_collisions=False
 for key in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,key,262144)
 env=task.Wall5CarryBoxEnv(cfg=cfg)
 try:
  expected=dict(ck['environment_contract'])
  if args.mode=='no_self':expected['self_collisions']=False
  assert env.checkpoint_contract()==expected
  wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=wrapped.reset()
  pc=agent.policy.to_dict();assert pc.pop('class_name')=='CarryBoxWall5ActorCritic'
  policy=CarryBoxWall5ActorCritic(obs,agent.obs_groups,29,**pc).to(args.device)
  policy.load_state_dict(ck['model_state_dict'],strict=True);policy.eval();saved={k:v.clone() for k,v in policy.state_dict().items()}
  env.set_training_iteration(0);env.set_training_iteration(S['checkpoint_iteration'])
  trace=JitterTrace(env,D,args.mode);rng=torch.load(D/'before_reset_rng.pt',weights_only=False)
  torch.set_rng_state(rng['cpu']);torch.cuda.set_rng_state(rng['cuda'])
  episodes=[];active=False;step=0;original=env._reset_idx
  def reset(ids):
   if active and getattr(env,'_carrybox_in_step',False):
    for i in ids.tolist():episodes.append(dict(env_id=i,end_step=step+1,steps=int(common.state(env).actual_episode_steps[i]),causes={n:bool(env.termination_manager.get_term(n)[i]) for n in env.termination_manager.active_terms}))
   original(ids)
   if args.mode=='no_delay':trace.term.delay.index[ids]=4
  with torch.inference_mode():
   obs,_=wrapped.reset()
   initial=trace.initial(obs);baseline=torch.load(D/'baseline_initial.pt',weights_only=False)
   max_errors={}
   for k,v in initial.items():
    if isinstance(v,dict):
     for n,x in v.items():
      torch.testing.assert_close(x,baseline[k][n],rtol=1e-5,atol=2e-5);max_errors['obs_'+n]=float((x-baseline[k][n]).abs().max())
    else:
     torch.testing.assert_close(v,baseline[k],rtol=1e-5,atol=2e-5);max_errors[k]=float((v-baseline[k]).abs().max())
   # Match simulation RNG after initial observations as well.
   if args.mode=='no_delay':trace.term.delay.index.fill_(4)
   env._reset_idx=reset;active=True;trace.active=True
   for step in range(1000):
    action=policy.act_inference(obs);trace.before(action)
    obs,reward,done,_=wrapped.step(action);trace.after(reward,done)
    assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
    if (step+1)%200==0:print('COMPARE_PROGRESS',args.mode,step+1,flush=True)
   trace.finish()
   assert all(torch.equal(v,saved[k]) for k,v in policy.state_dict().items())
  result=dict(status='PASS',mode=args.mode,initial_match_max_errors=max_errors,episodes=episodes,
   actual_contract=env.checkpoint_contract(),original_contract=ck['environment_contract'],
   override='self_collision=False' if args.mode=='no_self' else 'delay.index=4 at all resets; target pipeline otherwise unchanged',
   checkpoint=S['checkpoint'],checkpoint_sha256=S['checkpoint_sha256'],weights_unchanged=True,
   note='Same initial state/observations and deterministic mean policy, 20s closed loop; differing dynamics may cause trajectory divergence. Production untouched.')
  (D/f'{args.mode}.json').write_text(json.dumps(result,indent=2)+'\n')
  print('COMPARE_PASS',args.mode,flush=True)
 finally:env.close()
try:main()
except BaseException:
 import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
