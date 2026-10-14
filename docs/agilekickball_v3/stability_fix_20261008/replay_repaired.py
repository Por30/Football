"""Read-only matched-distribution diagnostic replay, not a general benchmark."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser(); AppLauncher.add_app_launcher_args(parser); args=parser.parse_args()
app=AppLauncher(args).app
env=None
import json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v3_env_cfg import AgileKickballV3EnvCfg, AgileKickballV3PPORunnerCfg
from perceptual_ball.rsl_rl_extensions.modules import PerceptionActorCritic
from perceptual_ball.rsl_rl_extensions.state_feedback import StateFeedbackActorCritic


def main():
 global env
 torch.set_num_threads(2)
 cfg=AgileKickballV3EnvCfg(); cfg.scene.num_envs=64; cfg.sim.device=args.device; cfg.seed=4208
 env=gym.make('Template-Perceptual-Ball-AgileKickball-v3',cfg=cfg)
 base=env.unwrapped; wrapped=RslRlVecEnvWrapper(env); kb=base._kickball
 agent=AgileKickballV3PPORunnerCfg(); policy_cfg=agent.policy.to_dict(); policy_cfg.pop('class_name')
 paths={'v2':'logs/rsl_rl/agilekickball_v2/2026-09-25_22-18-55_v1_speed_only_20260925_scratch/model_49999.pt',
        'v3':str(Path(json.loads(Path('docs/agilekickball_v3/stability_fix_20261008/scale_smoke.json').read_text())['run_dir'])/'model_99.pt')}
 report={'seed':4208,'num_envs':64,'control_steps_per_condition':1500,'control_dt_s':.02,
         'speed_range_m_s':[.4,2.],'distance_range_m':[1.3,2.],'conditions':{}}
 with torch.inference_mode():
  obs,_=wrapped.reset()
  for label,version,sampled,no_residual in [('repaired_after_100_updates_mean','v3',False,False)]:
   policy=(PerceptionActorCritic if version=='v2' else StateFeedbackActorCritic)(obs,agent.obs_groups,29,**policy_cfg).to(args.device)
   state=torch.load(paths[version],map_location=args.device,weights_only=False)
   policy.load_state_dict(state['model_state_dict']); policy.eval()
   if no_residual:
    policy.actor.residual[-1].weight.zero_(); policy.actor.residual[-1].bias.zero_()
   kb.curriculum_training=False; kb.course_exposure=60000.; kb.serve_speed_override=(.4,2.); kb._sync_course()
   torch.manual_seed(4208); obs,_=wrapped.reset()
   before=kb.metrics(); lengths=[]; terminations={key:0 for key in base.termination_manager.active_terms}
   elapsed=torch.zeros(64,device=args.device); reward_sum=0.; balanced=0.; contacts=0; actual_foot_proxy=0; base_action=0.; residual_abs=0.
   for step in range(1500):
    action=policy.act(obs) if sampled else policy.act_inference(obs)
    if version=='v3':
     features=policy._actor_features(obs)
     residual_abs+=float((policy.actor(features)-policy.actor.base(features[:,:policy.actor.feature_dim])).abs().mean())
    base_action+=float(action.abs().mean())
    obs,rewards,dones,_=wrapped.step(action)
    elapsed+=1; ids=dones.bool()
    lengths.extend(elapsed[ids].tolist()); elapsed[ids]=0
    reward_sum+=float(rewards.sum()); balanced+=int(kb.balanced().sum())
    contacts+=int(kb.kick_success_flag.sum())
    actual_foot_proxy+=int((kb.kick_success_flag & (kb.foot_ball_dist.amin(-1)<.3)).sum())
    for key in terminations:terminations[key]+=int((base.termination_manager.get_term(key)&ids).sum())
   after=kb.metrics()
   row={'checkpoint':paths[version],'sampled':sampled,'residual_disabled':no_residual,
        'episode_terminations':len(lengths),'completed_episode_mean_s':sum(lengths)/max(1,len(lengths))*.02,
        'right_censored_episodes':int((elapsed>0).sum()),'fresh_termination_counts':terminations,
        'new_serves':after['AgileKickball/serves']-before['AgileKickball/serves'],
        'recovered_serves':after['AgileKickball/recovered_serves']-before['AgileKickball/recovered_serves'],
        'kick_proxies':after['AgileKickball/kick_proxy_successes']-before['AgileKickball/kick_proxy_successes'],
        'observed_nonterminal_kick_pulses':contacts,'observed_pulses_with_foot_distance_lt_03':actual_foot_proxy,
        'balanced_frame_fraction':balanced/(64*1500),'task_reward_per_step':reward_sum/(64*1500),
        'action_abs_mean_raw':base_action/1500,'residual_abs_mean_raw':residual_abs/1500}
   report['conditions'][label]=row
   Path('docs/agilekickball_v3/stability_fix_20261008/replay_repaired.json').write_text(json.dumps(report,indent=2)+'\n')
   print('REPLAY',label,json.dumps(row),flush=True)

try:main()
except BaseException:
 import traceback,sys,os
 traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
finally:
 if env is not None:env.close()
 app.close(wait_for_replicator=False)
