"""Bounded real physics + PPO + full v3 transfer + versioned v4 resume."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app
env = None

import copy
import json
from pathlib import Path
import gymnasium as gym
import torch
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
from perceptual_ball.rsl_rl_extensions.state_feedback import StateFeedbackActorCritic
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v3_env_cfg import AgileKickballV3EnvCfg, AgileKickballV3PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v4_env_cfg import AgileKickballV4EnvCfg, AgileKickballV4PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v4 import REVISION

OUT = Path('docs/agilekickball_v4/return_to_sender_20261012')
SOURCE = Path('logs/rsl_rl/agilekickball_v3/2026-10-08_11-48-24_feedback_stable_20261008_v2init/model_49999.pt')


def main():
    global env
    torch.set_num_threads(2)
    cfg, agent = AgileKickballV4EnvCfg(), AgileKickballV4PPORunnerCfg()
    oldcfg, oldagent = AgileKickballV3EnvCfg(), AgileKickballV3PPORunnerCfg()
    assert agent.policy.to_dict() == oldagent.policy.to_dict()
    assert agent.algorithm.to_dict() == oldagent.algorithm.to_dict()
    old, new = oldcfg.to_dict(), cfg.to_dict()
    for row in (old, new):
        row['events'].pop('setup_kickball_state')
        for name in ('kick_return_task', 'kick_bonus', 'miss_penalty'): row['rewards'].pop(name)
    assert new['rewards'].pop('return_target_bonus')['weight'] == 150.
    assert old == new, 'Only startup and return rewards differ from stable v3'
    cfg.scene.num_envs = 16
    cfg.sim.device = args.device
    cfg.seed = 42
    agent.algorithm.num_learning_epochs = 1
    agent.algorithm.num_mini_batches = 1
    env = gym.make('Template-Perceptual-Ball-AgileKickball-v4', cfg=cfg)
    base = env.unwrapped
    wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
    kb = base._kickball
    runner = BallRegressionOnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
    with torch.inference_mode(): obs, _ = wrapped.reset()
    try:
        runner.load(str(SOURCE))
        raise AssertionError('Cross-version ordinary resume was accepted')
    except ValueError as error:
        assert 'v4 return curriculum' in str(error)
    runner.warm_start_from_v3(str(SOURCE))
    source = torch.load(SOURCE, map_location=args.device, weights_only=False)
    for key, value in runner.alg.policy.state_dict().items():
        torch.testing.assert_close(value, source['model_state_dict'][key], rtol=0, atol=0)
    for key, value in runner.alg.amp.state_dict().items():
        torch.testing.assert_close(value, source['amp_state_dict'][key], rtol=0, atol=0)
    policycfg = oldagent.policy.to_dict(); policycfg.pop('class_name')
    baseline = StateFeedbackActorCritic(obs, oldagent.obs_groups, 29, **policycfg).to(args.device)
    baseline.load_state_dict(source['model_state_dict'])
    with torch.no_grad():
        torch.testing.assert_close(runner.alg.policy.act_inference(obs), baseline.act_inference(obs), rtol=0, atol=0)
        torch.testing.assert_close(runner.alg.policy.evaluate(obs), baseline.evaluate(obs), rtol=0, atol=0)
    assert not runner.alg.optimizer.state and not runner.alg.ball_aux_optimizer.state and not runner.alg.amp_optimizer.state
    assert runner.current_learning_iteration == 0 and runner.alg.state_feedback_updates == 0
    assert kb.direction_steps == 0 and kb.course_steps == 0
    assert kb.serve_distance_range == (1.3, 2.) and kb.serve_speed_range == (.4, 1.1)
    torch.testing.assert_close(kb.source_xy, base.scene['ball'].data.root_pos_w[:, :2])
    replay = {}
    def rollout(label):
        with torch.inference_mode():
            torch.manual_seed(4212)
            current, _ = wrapped.reset()
            before = kb.metrics()
            terminations = 0
            for _ in range(1000):
                action = runner.alg.policy.act_inference(current)
                assert torch.isfinite(action).all()
                current, reward, done, info = wrapped.step(action)
                assert torch.isfinite(reward).all()
                terminations += int(done.sum())
            after = kb.metrics()
            result = {key: after[key] - before[key] for key in (
                'AgileKickball/recovered_serves', 'AgileV4/completed_rounds',
                'AgileV4/completed_target_hits', 'AgileV4/completed_strict_20cm_hits',
                'AgileV4/foot_strike_rounds')}
            assert result['AgileKickball/recovered_serves'] > 0, result
            assert result['AgileV4/completed_rounds'] > 0, result
            assert result['AgileV4/foot_strike_rounds'] > 0, result
            assert 0 <= result['AgileV4/completed_strict_20cm_hits'] <= result['AgileV4/completed_target_hits'] <= result['AgileV4/completed_rounds']
            replay[label] = dict(num_envs=16, control_steps=1000, seconds_per_env=20,
                                 fresh_terminations=terminations, counters=result)
            return wrapped.reset()[0]
    obs = rollout('v3_weights_before_updates')
    losses = []
    def update():
        nonlocal obs
        with torch.inference_mode():
            for _ in range(agent.num_steps_per_env):
                actions = runner.alg.act(obs)
                obs, rewards, dones, infos = wrapped.step(actions)
                runner.alg.process_env_step(obs, rewards, dones, infos)
            runner.alg.compute_returns(obs)
        result = runner.alg.update()
        assert all(torch.isfinite(torch.tensor(v)) for v in result.values()), result
        assert result['aux/predictor_updates'] > 0 and result['aux/encoder_updates'] == 0
        losses.append(result)
    for _ in range(2): update()
    runner.current_learning_iteration = 2
    checkpoint = OUT / 'smoke_model.pt'
    runner.save(str(checkpoint))
    saved_course = copy.deepcopy(kb.curriculum_state_dict())
    saved_updates = runner.alg.state_feedback_updates
    saved_optimizer = copy.deepcopy(runner.alg.ball_aux_optimizer.state_dict())
    runner = BallRegressionOnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
    runner.load(str(checkpoint), load_optimizer=True)
    assert kb.curriculum_state_dict() == saved_course
    assert runner.alg.state_feedback_updates == saved_updates
    actual_optimizer = runner.alg.ball_aux_optimizer.state_dict()
    assert actual_optimizer['param_groups'] == saved_optimizer['param_groups']
    for pid, values in saved_optimizer['state'].items():
        for key, value in values.items(): torch.testing.assert_close(actual_optimizer['state'][pid][key], value, rtol=0, atol=0)
    with torch.inference_mode(): obs, _ = wrapped.reset()
    update()
    obs = rollout('after_updates_and_resume')
    # Play-mode course must remain frozen even across real physics/reset calls.
    # Use a fresh play runner: training normalizers may hold inference-only buffers.
    runner = BallRegressionOnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
    runner.load(str(checkpoint), load_optimizer=False)
    frozen = copy.deepcopy(kb.curriculum_state_dict())
    with torch.inference_mode():
        obs, _ = wrapped.reset()
        for _ in range(24): obs, _, _, _ = wrapped.step(runner.alg.policy.act_inference(obs))
    assert kb.curriculum_state_dict() == frozen and not kb.curriculum_training
    result = dict(revision=REVISION, initialization=runner.warm_start_info,
                  complete_v3_policy_amp_and_initial_action_value_exact=True,
                  original_geometry_observation_algorithm_unchanged=True,
                  ppo_updates=3, losses=losses, replay=replay,
                  checkpoint_optimizer_and_course_roundtrip=True, play_course_frozen=True,
                  does_not_establish_learned_return_accuracy=True)
    (OUT / 'smoke.json').write_text(json.dumps(result, indent=2) + '\n')
    print('V4_SMOKE_PASS', json.dumps(result), flush=True)


try:
    main()
except BaseException:
    import traceback, sys, os
    traceback.print_exc(); sys.stdout.flush(); sys.stderr.flush(); os._exit(1)
finally:
    if env is not None: env.close()
    app.close(wait_for_replicator=False)
