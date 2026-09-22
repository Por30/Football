"""Bounded CPU checks: fresh PPO, course endpoints, checkpoint and recovery replay."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser);args=parser.parse_args()
app=AppLauncher(args).app;env=None
import json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_env_cfg import AgileKickballEnvCfg,AgileKickballPPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v1_env_cfg import AgileKickballV1EnvCfg,AgileKickballV1PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball import AgileKickballState
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner


def main():
    global env
    torch.set_num_threads(2)
    out=Path('docs/agilekickball_v1/simple_speed_validation');out.mkdir(parents=True,exist_ok=True)
    cfg,agent=AgileKickballV1EnvCfg(),AgileKickballV1PPORunnerCfg()
    v0=AgileKickballEnvCfg();v0agent=AgileKickballPPORunnerCfg()
    for key in ('observations','rewards','terminations','actions'):
        assert getattr(cfg,key).to_dict()==getattr(v0,key).to_dict(),key
    for key in ('algorithm','policy'):
        assert getattr(agent,key).to_dict()==getattr(v0agent,key).to_dict(),key
    cfg.scene.num_envs=16;cfg.sim.device=args.device;cfg.seed=42
    agent.num_steps_per_env=4;agent.algorithm.num_learning_epochs=1;agent.algorithm.num_mini_batches=1
    env=gym.make('Template-Perceptual-Ball-AgileKickball-v1',cfg=cfg)
    base=env.unwrapped;wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);kb=base._kickball
    runner=BallRegressionOnPolicyRunner(wrapped,agent.to_dict(),log_dir=None,device=args.device)
    # Actual new policy/optimizers: no loaded policy may stand in for scratch validation.
    with torch.inference_mode():
        obs,_=wrapped.reset();assert kb.ball_active.all()
        assert kb.serve_distance_range==(.5,.7) and kb.serve_speed_range==(.4,.8)
        for _ in range(4):
            action=runner.alg.act(obs);obs,reward,done,extras=wrapped.step(action)
            runner.alg.process_env_step(obs,reward,done,extras)
        runner.alg.compute_returns(obs)
    losses=runner.alg.update()
    assert all(torch.isfinite(torch.tensor(v)) for v in losses.values())
    assert losses['ball/incoming/count']>0
    runner.current_learning_iteration=1
    runner.save(str(out/'scratch_smoke_model.pt'))
    policy=runner.alg.policy.eval();sampling={}
    with torch.inference_mode():
        for exposure,upper in [(0,.8),(60000,1.1),(240000,2.),(360000,3.5),(480000,5.)]:
            data=kb.curriculum_state_dict();data['exposure_steps']=exposure
            kb.load_curriculum_state_dict(data);obs,_=wrapped.reset()
            speed=base.scene['ball'].data.root_lin_vel_w[:,:2].norm(dim=-1)
            assert ((speed>=.4-1.e-5)&(speed<=upper+1.e-5)).all()
            sampling[str(exposure)]={'min':speed.min().item(),'max':speed.max().item(),
                                    'distance_range':kb.serve_distance_range}
        assert sampling['480000']['max']>4.
        runner.save(str(out/'course_smoke_model.pt'));saved=kb.curriculum_state_dict()
        runner.load(str(out/'course_smoke_model.pt'),load_optimizer=False);obs,_=wrapped.reset()
        for _ in range(32):obs,_,_,_=wrapped.step(policy.act_inference(obs))
        assert saved==kb.curriculum_state_dict()
        kb.serve_speed_override=(1.,1.);kb._sync_course();obs,_=wrapped.reset()
        torch.testing.assert_close(base.scene['ball'].data.root_lin_vel_w[:,:2].norm(dim=-1),torch.ones(16),rtol=1.e-5,atol=1.e-5)
        # Same old standing policy, same speeds/distance, stochastic actions in both arms.
        # This is only a regression of recovery flow; it does not prove kicking competence.
        checkpoint=Path('logs/rsl_rl/agilekickball_v1/2026-09-21_12-52-45_success_curriculum_scratch/model_30600.pt')
        policy.load_state_dict(torch.load(checkpoint,map_location=args.device,weights_only=False)['model_state_dict'])
        policy.eval();replay={};new_balanced=kb.balanced
        for label in ('old_joint_gate','new_body_gate'):
            kb.balanced=AgileKickballState.balanced.__get__(kb) if label=='old_joint_gate' else new_balanced
            torch.manual_seed(922)
            data=kb.curriculum_state_dict();data['exposure_steps']=60000.
            kb.load_curriculum_state_dict(data);kb.curriculum_training=False
            kb.serve_speed_override=(.4,.8);kb._sync_course();obs,_=wrapped.reset()
            before=kb.metrics();done_count=0;waiting_count=0;body_pass=0;joint_pass=0;joint_sum=0.;stable_max=0.
            for _ in range(1000):
                wait=~kb.ball_active;q=base.scene['robot'].data
                rms=q.joint_vel.square().mean(-1).sqrt()
                waiting_count+=int(wait.sum());joint_sum+=float((rms*wait).sum())
                joint_pass+=int(((rms<1.5)&wait).sum());body_pass+=int((new_balanced()&wait).sum())
                stable_max=max(stable_max,float(kb.stable_elapsed.max()))
                obs,_,done,_=wrapped.step(policy.act(obs));done_count+=int(done.sum())
            after=kb.metrics()
            replay[label]={'checkpoint_policy_only':str(checkpoint),'steps':1000,'num_envs':16,
                           'speed_range':kb.serve_speed_range,'distance_range':kb.serve_distance_range,
                           'recovered_serves':after['AgileKickball/recovered_serves']-before['AgileKickball/recovered_serves'],
                           'episode_terminations':done_count,'waiting_samples':waiting_count,
                           'joint_rms_mean':joint_sum/max(waiting_count,1),
                           'joint_gate_pass_fraction':joint_pass/max(waiting_count,1),
                           'body_gate_pass_fraction':body_pass/max(waiting_count,1),'max_stable_interval_s':stable_max}
        kb.balanced=new_balanced
        assert replay['new_body_gate']['recovered_serves']>replay['old_joint_gate']['recovered_serves'],replay
        assert replay['new_body_gate']['episode_terminations']<replay['old_joint_gate']['episode_terminations'],replay
    result={'task':'Template-Perceptual-Ball-AgileKickball-v1','num_envs':16,'constructed_exposure_sampling':sampling,
            'scratch_ppo_updates':1,'scratch_losses':losses,'checkpoint_and_play_freeze':True,'fixed_speed_override':True,
            'v0_observations_rewards_terminations_actions_policy_algorithm_unchanged':True,'stochastic_recovery_replay':replay}
    (out/'smoke.json').write_text(json.dumps(result,indent=2)+'\n');print('V1_SIMPLE_SPEED_SMOKE_PASS',json.dumps(result),flush=True)

try:main()
except BaseException:
    import traceback,sys,os
    traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
finally:
    if env is not None:env.close()
    app.close(wait_for_replicator=False)
