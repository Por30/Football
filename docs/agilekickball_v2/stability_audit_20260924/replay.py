"""Read-only CPU replay of existing policies; no training, no production edits."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app;env=None
import torch,json,time
from pathlib import Path
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.managers import TerminationTermCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v2_env_cfg import AgileKickballV2EnvCfg,AgileKickballV2PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball import recovery_timed_out as old_timeout
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v1 import AgileKickballV1State
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v2 import AgileKickballV2State,recovery_timed_out as new_timeout
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner

def main():
 global env
 torch.set_num_threads(2)
 cfg=AgileKickballV2EnvCfg();cfg.scene.num_envs=16;cfg.sim.device='cpu';cfg.seed=42
 agent=AgileKickballV2PPORunnerCfg();agent.num_steps_per_env=4
 env=gym.make('Template-Perceptual-Ball-AgileKickball-v2',cfg=cfg);base=env.unwrapped
 wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
 runner=BallRegressionOnPolicyRunner(wrapped,agent.to_dict(),log_dir=None,device='cpu');policy=runner.alg.policy
 paths={'v1_10000':'logs/rsl_rl/agilekickball_v1/2026-09-22_14-41-48_success_curriculum_scratch/model_10000.pt',
        'v1_47400':'logs/rsl_rl/agilekickball_v1/2026-09-22_14-41-48_success_curriculum_scratch/model_47400.pt',
        'v2_10400':'logs/rsl_rl/agilekickball_v2/2026-09-24_03-53-05_success_curriculum_scratch/model_10400.pt'}
 rows=[]
 with torch.inference_mode():
  for label,path in paths.items():
   policy.load_state_dict(torch.load(path,map_location='cpu',weights_only=False)['model_state_dict']);policy.eval()
   for arm,cls,timeout,distance in [('v1_recovery',AgileKickballV1State,old_timeout,(1.3,2.)),('v2_recovery',AgileKickballV2State,new_timeout,(1.3,2.)),('v2_short_distance',AgileKickballV2State,new_timeout,(.5,.7))]:
    kb=cls(base);base._kickball=kb;kb.curriculum_training=False
    # Freeze identical served speeds and distances. This is inference-only counterfactual replay.
    kb._sync_course=lambda:None;kb.serve_speed_override=(.4,1.45);kb.serve_speed_range=(.4,1.45);kb.serve_distance_range=distance
    base.termination_manager.set_term_cfg('recovery_timeout',TerminationTermCfg(func=timeout))
    torch.manual_seed(924);obs,_=wrapped.reset();before=kb.metrics();term_counts={k:0 for k in base.termination_manager.active_terms}
    steps=800;wait=0;proxy=0;foot_proxy=0;active_foot_proxy=0;dist_sum=0.;elapsed_sum=0.;done_count=0;drift_sum=0.;hold_sum=0.;max_hold_count=0;start=time.monotonic()
    # Counterfactual V1 readiness monitors on the SAME v2 physical trajectories.
    old_wait=torch.zeros(16);old_stable=torch.zeros(16);old_ready_blocked=0;clock_blocked=0
    for i in range(steps):
     old_wait=torch.where(~kb.ball_active,old_wait+base.step_dt,0.)
     old_stable=torch.where(~kb.ball_active & AgileKickballV1State.balanced(kb),old_stable+base.step_dt,0.)
     duration=base.episode_length_buf.clone()*base.step_dt
     obs,rew,done,infos=wrapped.step(policy.act_inference(obs))
     wait+=int((~kb.ball_active).sum());done_count+=int(done.sum());elapsed_sum+=float(duration[done.bool()].sum())
     for key in term_counts:term_counts[key]+=int((base.termination_manager.get_term(key) & done.bool()).sum())
     flag=kb.kick_success_flag;proxy+=int(flag.sum());nearest,ix=kb.foot_ball_dist.min(-1);near=flag & (nearest<.3)
     foot_proxy+=int(near.sum());dist_sum+=float(nearest[flag].sum())
     xy=kb.ball.data.root_pos_w[:,:2]-kb.anchor_xy;direction=xy/xy.norm(dim=-1,keepdim=True).clamp(min=1.e-6)
     feet_v=kb.robot.data.body_link_lin_vel_w[:,kb.foot_body_ids,:2][torch.arange(16),ix]
     active_foot_proxy+=int((near & (((feet_v-kb.robot.data.root_lin_vel_w[:,:2])*direction).sum(-1)>.5)).sum())
     drift_sum+=float((kb.robot.data.root_pos_w[:,:2]-kb.anchor_xy).norm(dim=-1).sum())
     if cls is AgileKickballV2State:
      hold_sum+=float(kb.required_hold.sum());max_hold_count+=int((kb.required_hold>=.399).sum())
      was_ready=(~kb.ball_active)&(old_wait>=.4)&(old_stable>=.3)&(~done.bool())
      old_ready_blocked+=int((was_ready & (kb.stable_elapsed<kb.required_hold)).sum())
      clock_blocked+=int((was_ready & (kb.recovery_elapsed>=5.)).sum())
     old_wait[done.bool()]=0;old_stable[done.bool()]=0
    after=kb.metrics();served=after['AgileKickball/serves']-before['AgileKickball/serves'];recovered=after['AgileKickball/recovered_serves']-before['AgileKickball/recovered_serves']
    result={'policy':label,'checkpoint':path,'arm':arm,'seed':924,'num_envs':16,'steps':steps,'speed_range':[.4,1.45],'distance_range':distance,'episode_terminations':done_count,'ended_episode_mean_s':elapsed_sum/max(1,done_count),'terminal_counts':term_counts,'additional_serves':served,'recovered_serves':recovered,'kick_proxy_pulses':proxy,'foot_near_proxy_pulses':foot_proxy,'active_foot_proxy_pulses':active_foot_proxy,'nearest_foot_distance_at_proxy_mean_m':dist_sum/max(1,proxy),'waiting_fraction':wait/(steps*16),'anchor_drift_mean_m':drift_sum/(steps*16),'hold_mean_s':hold_sum/(steps*16),'hold_at_cap_fraction':max_hold_count/(steps*16),'old_ready_blocked_by_v2_hold_samples':old_ready_blocked,'old_ready_blocked_by_v2_clock_samples':clock_blocked,'wall_seconds':time.monotonic()-start}
    assert sum(term_counts.values()) == done_count, (term_counts, done_count)
    rows.append(result);Path('docs/agilekickball_v2/stability_audit_20260924/replay.json').write_text(json.dumps(rows,indent=2));print('ARM_RESULT',json.dumps(result),flush=True)
 print('READ_ONLY_REPLAY_COMPLETE',flush=True)
try:main()
except BaseException:
 import traceback,sys,os
 traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
finally:
 if env is not None:env.close()
 app.close(wait_for_replicator=False)
