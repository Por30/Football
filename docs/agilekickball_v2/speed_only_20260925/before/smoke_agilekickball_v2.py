"""Bounded real CPU simulation, separate from constructed state-machine unit tests."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser);args=parser.parse_args()
app=AppLauncher(args).app;env=None
import json
import time
from pathlib import Path
import gymnasium as gym
import torch
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v1_env_cfg import AgileKickballV1EnvCfg, AgileKickballV1PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v2_env_cfg import AgileKickballV2EnvCfg, AgileKickballV2PPORunnerCfg
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner


def main():
    global env
    torch.set_num_threads(2);out=Path('docs/agilekickball_v2/stability_fix_20260924/validation');out.mkdir(parents=True,exist_ok=True)
    cfg,agent=AgileKickballV2EnvCfg(),AgileKickballV2PPORunnerCfg()
    v1,a1=AgileKickballV1EnvCfg(),AgileKickballV1PPORunnerCfg()
    for key in ('observations','actions'):
        assert getattr(cfg,key).to_dict()==getattr(v1,key).to_dict(),key
    for key in ('policy','algorithm'):
        assert getattr(agent,key).to_dict()==getattr(a1,key).to_dict(),key
    assert cfg.rewards.kick_bonus.weight==100. and cfg.rewards.joint_return_bonus.weight==400.
    assert cfg.rewards.failure_penalty.weight==-400.
    assert v1.rewards.kick_bonus.weight==300.
    assert cfg.rewards.kickball_tick.weight!=0
    cfg.scene.num_envs=16;cfg.sim.device=args.device;cfg.seed=42
    agent.num_steps_per_env=8;agent.algorithm.num_learning_epochs=1;agent.algorithm.num_mini_batches=1
    env=gym.make('Template-Perceptual-Ball-AgileKickball-v2',cfg=cfg)
    base=env.unwrapped;wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);kb=base._kickball
    runner=BallRegressionOnPolicyRunner(wrapped,agent.to_dict(),log_dir=None,device=args.device)
    with torch.inference_mode():
        obs,_=wrapped.reset()
        assert kb.ball_active.all() and kb.serve_speed_range==(.4,.8)
    scratch_losses=[]
    for update in range(4):
        with torch.inference_mode():
            for _ in range(8):
                actions=runner.alg.act(obs);obs,rewards,dones,infos=wrapped.step(actions)
                runner.alg.process_env_step(obs,rewards,dones,infos)
            runner.alg.compute_returns(obs)
        losses=runner.alg.update()
        assert all(torch.isfinite(torch.tensor(v)) for v in losses.values()),losses
        scratch_losses.append(losses)
    assert sum(x['ball/incoming/count'] for x in scratch_losses)>0
    runner.current_learning_iteration=1
    runner.save(str(out/'scratch.pt'))
    sampling={}
    with torch.inference_mode():
        for steps,upper in [(0,.8),(120000,.8),(360000,2.),(720000,5.),(840000,6.)]:
            state=kb.curriculum_state_dict();state['control_steps']=steps;kb.load_curriculum_state_dict(state)
            obs,_=wrapped.reset();speed=base.scene['ball'].data.root_lin_vel_w[:,:2].norm(dim=-1)
            assert ((speed>=.4-1.e-5)&(speed<=upper+1.e-5)).all(),speed
            dist=(base.scene['ball'].data.root_pos_w[:,:2]-kb.anchor_xy).norm(dim=-1)
            extension=.3*(speed-.8).clamp(0.,5.2)
            assert ((dist>=.5+extension-1.e-5)&(dist<=.7+extension+1.e-5)).all()
            assert kb._pending_serve_speed is None
            sampling[str(steps)]={'min_m_s':speed.min().item(),'max_m_s':speed.max().item(),
                                  'distance_range_m':kb.serve_distance_range}
        runner.save(str(out/'course.pt'));saved=kb.curriculum_state_dict()
        runner.load(str(out/'course.pt'),load_optimizer=False);obs,_=wrapped.reset()
        for _ in range(32):obs,_,_,_=wrapped.step(runner.alg.policy.act_inference(obs))
        assert saved==kb.curriculum_state_dict()
        # Same physical speed/distance distribution: reward stable returns over kick-and-run.
        paths={'stable_v1':Path('logs/rsl_rl/agilekickball_v1/2026-09-22_14-41-48_success_curriculum_scratch/model_47400.pt'),
               'unstable_old_v2':Path('logs/rsl_rl/agilekickball_v2/2026-09-24_03-53-05_success_curriculum_scratch/model_10400.pt')}
        replay={}
        for label,checkpoint in paths.items():
            runner.alg.policy.load_state_dict(torch.load(checkpoint,map_location=args.device,weights_only=False)['model_state_dict'])
            runner.alg.policy.eval();kb.serve_speed_override=(.4,1.45)
            torch.manual_seed(924);obs,_=wrapped.reset();before=kb.metrics();wins_before=int(kb.joint_success.sum())
            start=time.monotonic();done_count=0;reward_sum=0.;failures=0
            for _ in range(1000):
                obs,reward,done,_=wrapped.step(runner.alg.policy.act_inference(obs))
                done_count+=int(done.sum());reward_sum+=float(reward.sum())
                failures+=int(base.termination_manager.terminated.sum())
            after=kb.metrics()
            assert kb.serves.sum()==kb.closed.sum()+kb.censored.sum()+kb.round_open.sum()
            replay[label]={'checkpoint_policy_only':str(checkpoint),'num_envs':16,'control_steps':1000,
                'elapsed_s':time.monotonic()-start,'speed_range_m_s':[.4,1.45],
                'recovered_serves':after['AgileKickball/recovered_serves']-before['AgileKickball/recovered_serves'],
                'episode_terminations':done_count,'failure_penalties':failures,
                'strict_joint_successes':int(kb.joint_success.sum())-wins_before,
                'task_reward_per_env_step':reward_sum/16000.}
        assert replay['stable_v1']['strict_joint_successes']>0,replay
        assert replay['stable_v1']['recovered_serves']>replay['unstable_old_v2']['recovered_serves'],replay
        assert replay['stable_v1']['task_reward_per_env_step']>replay['unstable_old_v2']['task_reward_per_env_step'],replay
        assert replay['unstable_old_v2']['failure_penalties']>0,replay
        runner.alg.policy.load_state_dict(torch.load(paths['stable_v1'],map_location=args.device,weights_only=False)['model_state_dict'])
        # Freshly served 6m/s balls in actual physics + actual synthetic camera frames.
        kb.serve_speed_override=(6.,6.)
        state=kb.curriculum_state_dict();state['control_steps']=840000;kb.load_curriculum_state_dict(state)
        obs,_=wrapped.reset()
        speed=base.scene['ball'].data.root_lin_vel_w[:,:2].norm(dim=-1)
        torch.testing.assert_close(speed,torch.full_like(speed,6.),atol=1.e-5,rtol=1.e-5)
        manager=base.observation_manager
        term=manager._group_obs_term_cfgs['perception'][manager.active_terms['perception'].index('depth_image')]
        seen=torch.zeros(16,dtype=torch.bool,device=args.device);counts=torch.zeros(16,device=args.device)
        initial_visible=None
        for i in range(20):
            depth=term.func(base,**term.params);visible=(depth<term.params['far']-1.e-4).flatten(1).any(-1)
            if i==0:initial_visible=int(visible.sum())
            status=kb.observation_status();eligible=status[:,1].bool() & ~status[:,2].bool()
            seen|=visible & eligible;counts+=visible & eligible
            obs,_,_,_=wrapped.step(runner.alg.policy.act_inference(obs))
        assert seen.all(),seen
        visibility={'fixed_speed_m_s':6.,'distance_range_m':kb.serve_distance_range,'initial_visible_envs':initial_visible,
                    'seen_before_near_foot_envs':int(seen.sum()),'visible_incoming_control_frames_mean':counts.mean().item(),
                    'num_envs':16,'control_steps':20,'synthetic_camera_no_occlusion':True}
    result={'scratch_ppo_updates':4,'scratch_losses':scratch_losses,'constructed_course_sampling':sampling,
            'policy_algorithm_observations_unchanged_from_v1':True,
            'event_rewards_before_amp':{'active_kick':2.,'stable_return':8.,'failure':-8.},
            'event_rewards_after_task_mixing':{'active_kick':1.5,'stable_return':6.,'failure':-6.},'checkpoint_freeze_and_override':True,
            'physical_recovery_replay':replay,'high_speed_visibility':visibility,
            'does_not_establish_high_speed_skill_or_research_claim':True}
    (out/'smoke.json').write_text(json.dumps(result,indent=2)+'\n')
    print('V2_RECOVERY_SMOKE_PASS',json.dumps(result),flush=True)

try:main()
except BaseException:
    import traceback,sys,os
    traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
finally:
    if env is not None:env.close()
    app.close(wait_for_replicator=False)
