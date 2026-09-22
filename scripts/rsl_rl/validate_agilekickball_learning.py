"""Bounded real simulator training plus fixed held-out and fresh-seed evaluation."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app
env = None

import json
import time
from pathlib import Path
import torch
from tensordict import TensorDict
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_env_cfg import AgileKickballEnvCfg, AgileKickballPPORunnerCfg
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
from perceptual_ball.rsl_rl_extensions.ball_metrics import ball_prediction_metrics


def main():
    global env
    torch.set_num_threads(2)
    out = Path('docs/agilekickball/learning_validation')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'result.json').unlink(missing_ok=True)
    cfg, agent = AgileKickballEnvCfg(), AgileKickballPPORunnerCfg()
    cfg.scene.num_envs = 16
    cfg.sim.device = args.device
    cfg.seed = 42
    agent.device = args.device
    agent.algorithm.num_learning_epochs = 1
    # Aux uses all 4 minibatches once; architecture and AMP remain the task defaults.
    env = gym.make('Template-Perceptual-Ball-AgileKickball-v0', cfg=cfg)
    base = env.unwrapped
    wrapper = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
    runner = BallRegressionOnPolicyRunner(wrapper, agent.to_dict(), log_dir=None, device=args.device)
    policy = runner.alg.policy
    kb = base._kickball

    def collect(seed, steps=96):
        torch.manual_seed(seed)
        policy.eval()
        batches, dones_total = [], 0
        with torch.inference_mode():
            obs, _ = wrapper.reset()
            assert kb.ball_active.all()
            for _ in range(steps):
                batches.append(obs.clone())  # action-time status and newest depth align
                obs, _, done, _ = wrapper.step(policy.act_inference(obs))
                dones_total += int(done.sum())
        # Materialize normal tensors outside inference mode for later supervised forwards.
        data = torch.cat(batches, dim=0).clone()
        return data, dones_total

    heldout, heldout_dones = collect(1731)
    before = ball_prediction_metrics(policy, heldout)
    print('HELDOUT_BEFORE', json.dumps(before), flush=True)
    assert before['incoming/count'] > 0 and before['active_visible/count'] > 0
    assert before['near_foot/count'] > 0, 'No physical approach enters the interaction region'
    old_checkpoint = Path('logs/rsl_rl/agilekickball_v0/2026-09-20_13-00-03_speed_curriculum/model_5400.pt')
    old_metrics = None
    if old_checkpoint.exists():
        saved = {k: v.clone() for k, v in policy.state_dict().items()}
        policy.load_state_dict(torch.load(old_checkpoint, weights_only=False, map_location=args.device)['model_state_dict'])
        old_metrics = ball_prediction_metrics(policy, heldout)
        policy.load_state_dict(saved)
        print('OLD_CHECKPOINT_HELDOUT', json.dumps(old_metrics), flush=True)
    torch.manual_seed(42)
    with torch.inference_mode():
        obs, _ = wrapper.reset()
    policy.train()
    encoder_start = [p.detach().clone() for p in policy.perception_encoder.parameters()]
    history = []
    start = time.monotonic()
    for iteration in range(32):
        with torch.inference_mode():
            for _ in range(agent.num_steps_per_env):
                action = runner.alg.act(obs)
                obs, reward, done, extras = wrapper.step(action)
                runner.alg.process_env_step(obs, reward, done, extras)
            runner.alg.compute_returns(obs)
        losses = runner.alg.update()
        assert all(torch.isfinite(torch.tensor(v)) for v in losses.values()), losses
        assert losses['ball/incoming/count'] > 0, 'A training rollout contains no approaching balls'
        assert losses['aux/encoder_updates'] + losses['aux/head_only_batches'] == 4
        history.append(losses)
        print('UPDATE', iteration, json.dumps(losses), flush=True)
        assert time.monotonic() - start < 900, 'Bounded training exceeded 15 minutes'
    policy.eval()
    after = ball_prediction_metrics(policy, heldout)
    fresh, fresh_dones = collect(9271)
    fresh_metrics = ball_prediction_metrics(policy, fresh)
    assert fresh_metrics['incoming/count'] > 0 and fresh_metrics['near_foot/count'] > 0
    assert sum(x['aux/encoder_updates'] for x in history) > 0
    encoder_delta = sum((a - b).square().sum().item() for a, b in zip(encoder_start, policy.perception_encoder.parameters())) ** .5
    assert encoder_delta > 0
    assert after['active_visible/position_cm_rmse'] < before['active_visible/position_cm_rmse'], 'Held-out position did not improve'
    runner.save(str(out / 'model_validation.pt'))
    exposure = kb.exposure_steps
    # Test restoring exposure as well as shared optimizers, without changing sample state.
    kb.exposure_offset = -999.
    with torch.inference_mode():
        runner.load(str(out / 'model_validation.pt'))
    assert abs(kb.exposure_steps - exposure) < 1.e-4
    result = dict(task='Template-Perceptual-Ball-AgileKickball-v0', num_envs=16, updates=32,
        seed_train=42, seed_heldout=1731, seed_fresh=9271, train_seconds=time.monotonic()-start,
        before=before, after_same_heldout=after, fresh_evaluation=fresh_metrics,
        old_checkpoint=str(old_checkpoint) if old_metrics else None, old_checkpoint_same_heldout=old_metrics,
        heldout_resets=heldout_dones, fresh_eval_resets=fresh_dones, encoder_parameter_l2_change=encoder_delta,
        update_history=history, counters=kb.metrics(), checkpoint_roundtrip=True,
        scope='Engineering validation, 16 environments / 32 updates; not kick convergence or real-world accuracy')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('VALIDATION_COMPLETE', json.dumps({k:v for k,v in result.items() if k != 'update_history'}), flush=True)


try:
    main()
except BaseException:
    import traceback
    traceback.print_exc()
    import sys, os
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)  # Kit may swallow exceptions or hang closing a partially created scene.
finally:
    if env is not None:
        env.close()
    app.close(wait_for_replicator=False)
