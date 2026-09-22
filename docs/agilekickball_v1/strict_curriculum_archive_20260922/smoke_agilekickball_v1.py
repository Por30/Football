"""Real-simulator sampling, checkpoint, natural recovery, and one PPO update."""
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
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_env_cfg import AgileKickballEnvCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v1_env_cfg import AgileKickballV1EnvCfg, AgileKickballV1PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v1 import STAGE_UPPERS
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner


def main():
    global env
    torch.set_num_threads(2)
    out=Path('docs/agilekickball_v1/validation');out.mkdir(parents=True,exist_ok=True)
    cfg,agent=AgileKickballV1EnvCfg(),AgileKickballV1PPORunnerCfg()
    v0=AgileKickballEnvCfg()
    for key in ('observations','rewards','terminations','actions'):
        assert getattr(cfg,key).to_dict()==getattr(v0,key).to_dict(),key
    cfg.scene.num_envs=16;cfg.sim.device=args.device;cfg.seed=42
    agent.num_steps_per_env=4;agent.algorithm.num_learning_epochs=1;agent.algorithm.num_mini_batches=1
    env=gym.make('Template-Perceptual-Ball-AgileKickball-v1',cfg=cfg)
    base=env.unwrapped;wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);kb=base._kickball
    runner=BallRegressionOnPolicyRunner(wrapped,agent.to_dict(),log_dir=None,device=args.device)
    v0checkpoint=Path('logs/rsl_rl/agilekickball_v0/2026-09-20_18-02-42_learning_fix/model_25200.pt')
    runner.load(str(v0checkpoint),load_optimizer=True)
    assert kb.stage==0 and kb.window['total']==0 and kb.curriculum_training
    policy=runner.alg.policy.eval()
    sampling={}
    with torch.inference_mode():
        for stage,upper in enumerate(STAGE_UPPERS):
            # Explicitly constructed course states test endpoints, not achieved competence.
            state=kb.curriculum_state_dict();state['stage']=stage
            kb.load_curriculum_state_dict(state);obs,_=wrapped.reset()
            speed=base.scene['ball'].data.root_lin_vel_w[:,:2].norm(dim=-1)
            torch.testing.assert_close(speed,kb.round_speed)
            assert ((speed>=.4-1.e-5)&(speed<=upper+1.e-5)).all()
            sampling[str(stage)]={'min':speed.min().item(),'max':speed.max().item(),'challenge':int(kb.round_challenge.sum())}
        assert sampling['9']['max']>4.5
        fast_initial=base.scene['ball'].data.root_lin_vel_w[:,:2].norm(dim=-1).tolist()
        for _ in range(64):obs,_,_,_=wrapped.step(policy.act_inference(obs))
        fast_counters=kb.metrics()
        # Start v1 at stage0 with the old v0 policy; never import its exposure-based stage.
        runner.load(str(v0checkpoint),load_optimizer=True);obs,_=wrapped.reset()
        start_serves=int(kb.serves.sum());start_settled=kb.settled_total;start_success=kb.strict_success_total
        before_rounds=int(kb.round_open.sum());done_total=0
        for _ in range(400):
            obs,_,done,_=wrapped.step(policy.act_inference(obs));done_total+=int(done.sum())
        settled=kb.settled_total-start_settled;success=kb.strict_success_total-start_success
        assert settled>0
        assert int(kb.serves.sum())-start_serves==settled+int(kb.round_open.sum())-before_rounds
        natural={'settled':settled,'strict_proxy_successes':success,'success_rate':success/settled,
                 'episode_resets':done_total,'stage':kb.stage,'window':kb.window.copy()}
        assert kb.stage==0,'Smoke window must not pretend to prove stage mastery'
        # Exact curriculum state roundtrip; eval load must freeze its windows/residence.
        runner.save(str(out/'smoke_model.pt'))
        saved=kb.curriculum_state_dict()
        runner.load(str(out/'smoke_model.pt'),load_optimizer=False);obs,_=wrapped.reset()
        for _ in range(32):obs,_,_,_=wrapped.step(policy.act_inference(obs))
        for key in ('stage','stage_steps','passing_windows','window','last_window'):
            assert kb.curriculum_state_dict()[key]==saved[key],key
    # Optimizer state must be loaded outside inference mode before gradient updates.
    runner.load(str(out/'smoke_model.pt'),load_optimizer=True)
    with torch.inference_mode():
        obs,_=wrapped.reset()
    policy.train()
    with torch.inference_mode():
        for _ in range(4):
            action=runner.alg.act(obs);obs,reward,done,extras=wrapped.step(action)
            runner.alg.process_env_step(obs,reward,done,extras)
        runner.alg.compute_returns(obs)
    losses=runner.alg.update()
    assert all(torch.isfinite(torch.tensor(v)) for v in losses.values())
    result={'task':'Template-Perceptual-Ball-AgileKickball-v1','num_envs':16,'sampling_constructed_stages':sampling,
            'five_m_s_stage_initial_velocities':fast_initial,'fast_stage_counters_not_performance_claim':fast_counters,
            'natural_stage0_with_v0_policy':natural,'v0_checkpoint':str(v0checkpoint),'checkpoint_and_play_freeze':True,
            'v0_observations_rewards_terminations_actions_unchanged':True,'ppo_updates':1,'losses':losses}
    (out/'smoke.json').write_text(json.dumps(result,indent=2)+'\n');print('V1_SMOKE_PASS',json.dumps(result),flush=True)

try:main()
except BaseException:
    import traceback,sys,os
    traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
finally:
    if env is not None:env.close()
    app.close(wait_for_replicator=False)
