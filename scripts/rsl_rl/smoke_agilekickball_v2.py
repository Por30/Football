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
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v1 import AgileKickballV1State
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v2 import AgileKickballV2State, REVISION


def main():
    global env
    torch.set_num_threads(2);out=Path('docs/agilekickball_v2/speed_only_20260925/validation');out.mkdir(parents=True,exist_ok=True)
    cfg,agent=AgileKickballV2EnvCfg(),AgileKickballV2PPORunnerCfg()
    v1,a1=AgileKickballV1EnvCfg(),AgileKickballV1PPORunnerCfg()
    c1,c2=v1.to_dict(),cfg.to_dict()
    c1['events'].pop('setup_kickball_state');c2['events'].pop('setup_kickball_state')
    assert c1==c2, 'V2 must preserve all v1 configuration except startup'
    r1,r2=a1.to_dict(),agent.to_dict();r1.pop('experiment_name');r2.pop('experiment_name')
    assert r1==r2, 'V2 must preserve the entire v1 runner configuration'
    assert cfg.events.setup_kickball_state.params['revision']==REVISION
    assert cfg.rewards.kick_bonus.weight==300.
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
        for exposure,unlocked,progress,upper in [(0.,False,0.,.8),(60000.,False,0.,1.1),
                                                       (60000.,True,.5,3.55),(60000.,True,1.,6.)]:
            state=kb.curriculum_state_dict()
            state.update(exposure_steps=exposure,extension_unlocked=unlocked,extension_start_upper=1.1,
                         extension_steps=288000*progress,advance_rate=0.)
            kb.load_curriculum_state_dict(state)
            obs,_=wrapped.reset();speed=base.scene['ball'].data.root_lin_vel_w[:,:2].norm(dim=-1)
            assert ((speed>=.4-1.e-5)&(speed<=upper+1.e-5)).all(),speed
            dist=(base.scene['ball'].data.root_pos_w[:,:2]-kb.anchor_xy).norm(dim=-1)
            low,high=kb.serve_distance_range
            assert ((dist>=low-1.e-5)&(dist<=high+1.e-5)).all()
            sampling[str(upper)]={'min_m_s':speed.min().item(),'max_m_s':speed.max().item(),
                                  'distance_range_m':kb.serve_distance_range}
        runner.save(str(out/'course.pt'));saved=kb.curriculum_state_dict()
        runner.load(str(out/'course.pt'),load_optimizer=False);obs,_=wrapped.reset()
        for _ in range(32):obs,_,_,_=wrapped.step(runner.alg.policy.act_inference(obs))
        assert saved==kb.curriculum_state_dict()
        # Same mature v1 policy and physical distribution, then latest failed v2 policy.
        stable=Path('logs/rsl_rl/agilekickball_v1/2026-09-22_14-41-48_success_curriculum_scratch/model_47400.pt')
        unstable=Path('logs/rsl_rl/agilekickball_v2/2026-09-24_15-01-01_stability_fix_scratch/model_40800.pt')
        replay={}
        for label,checkpoint,state_type in [('v1_reference',stable,AgileKickballV1State),
                ('v2_with_v1_policy',stable,AgileKickballV2State),('v2_with_old_failed_policy',unstable,AgileKickballV2State)]:
            base._kickball=kb=state_type(base)
            kb.curriculum_training=False;kb.course_exposure=146000.
            kb.serve_speed_override=(.4,1.528);kb._sync_course()
            runner.alg.policy.load_state_dict(torch.load(checkpoint,map_location=args.device,weights_only=False)['model_state_dict'])
            runner.alg.policy.eval();torch.manual_seed(925)
            obs,_=wrapped.reset();before=kb.metrics()
            start=time.monotonic();done_count=0;reward_sum=0.
            terminations={name:0 for name in base.termination_manager.active_terms}
            for _ in range(1000):
                obs,reward,done,_=wrapped.step(runner.alg.policy.act_inference(obs))
                done_count+=int(done.sum());reward_sum+=float(reward.sum())
                for name in terminations:
                    terminations[name]+=int((base.termination_manager.get_term(name)&done.bool()).sum())
            after=kb.metrics()
            replay[label]={'checkpoint_policy_only':str(checkpoint),'num_envs':16,'control_steps':1000,
                'elapsed_s':time.monotonic()-start,'speed_range_m_s':[.4,1.528],
                'recovered_serves':after['AgileKickball/recovered_serves']-before['AgileKickball/recovered_serves'],
                'kick_proxy_successes':after['AgileKickball/kick_proxy_successes']-before['AgileKickball/kick_proxy_successes'],
                'new_serves':after['AgileKickball/serves']-before['AgileKickball/serves'],
                'episode_terminations':done_count,'termination_counts_masked_by_done':terminations,
                'task_reward_per_env_step':reward_sum/16000.}
        assert replay['v1_reference']['recovered_serves']>0,replay
        assert replay['v2_with_v1_policy']['recovered_serves']>0,replay
        runner.alg.policy.load_state_dict(torch.load(stable,map_location=args.device,weights_only=False)['model_state_dict'])
        # Freshly served 6m/s balls in actual physics + actual synthetic camera frames.
        kb.serve_speed_override=(6.,6.)
        state=kb.curriculum_state_dict();state.update(extension_unlocked=True,extension_start_upper=1.1,extension_steps=288000.);kb.load_curriculum_state_dict(state)
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
    result={'revision':REVISION,'scratch_ppo_updates':4,'scratch_losses':scratch_losses,
            'constructed_course_sampling':sampling,'entire_v1_env_except_startup_and_runner_except_name_unchanged':True,
            'checkpoint_freeze_and_override':True,'physical_recovery_replay':replay,'high_speed_visibility':visibility,
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
