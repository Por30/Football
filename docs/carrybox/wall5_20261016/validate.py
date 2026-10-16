"""4-env stage-A integration, production PPO sizes; no formal training or performance claim."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app
import copy
import json
from pathlib import Path
import torch
import gymnasium as gym
import onnx
import perceptual_ball.tasks
from isaaclab_tasks.utils.parse_cfg import load_cfg_from_registry
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg, CarryBoxWalled4PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy

OUT = Path(__file__).resolve().parent
TASK = 'Template-Perceptual-Ball-CarryBox-Walled5-v0'


def differences(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        return sum([differences(a.get(k), b.get(k), path + '.' + k) for k in set(a) | set(b)], [])
    return [] if str(a) == str(b) else [path]


def main():
    torch.set_num_threads(2)
    cfg = load_cfg_from_registry(TASK, 'env_cfg_entry_point')
    agent = load_cfg_from_registry(TASK, 'rsl_rl_cfg_entry_point')
    old, old_agent = CarryBoxWalled4EnvCfg(), CarryBoxWalled4PPORunnerCfg()
    env_diff = differences(old.to_dict(), cfg.to_dict())
    alg_diff = differences(old_agent.to_dict(), agent.to_dict())
    assert set(env_diff) == {'.walled_variant', '.observations.amp.motion.func'}, env_diff
    assert set(alg_diff) == {'.class_name', '.experiment_name', '.run_name', '.algorithm.class_name', '.algorithm.amp_reward_scale', '.algorithm.amp_lr'}, alg_diff
    assert cfg.scene.depth_camera.object_names == old.scene.depth_camera.object_names
    assert cfg.obstacle_cylinder_count == 3
    assert agent.algorithm.learning_rate == 3e-4 and agent.algorithm.schedule == 'fixed'
    assert agent.algorithm.num_learning_epochs == 4 and agent.algorithm.num_mini_batches == 4
    assert agent.policy.init_noise_std == .2
    assert 'agilekickball_v4_env_cfg' in gym.spec('Template-Perceptual-Ball-AgileKickball-v4').kwargs['env_cfg_entry_point']
    assert 'carrybox_walled_env_cfg' in gym.spec('Template-Perceptual-Ball-CarryBox-Walled4-v0').kwargs['env_cfg_entry_point']
    cfg.scene.num_envs = 4
    cfg.seed = 42
    cfg.sim.device = args.device
    env = gym.make(TASK, cfg=cfg)
    try:
        b = env.unwrapped
        w = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        done_count = 0
        with torch.inference_mode():
            obs, _ = w.reset()
            assert tuple(obs['amp'].shape) == (4, 350)
            assert tuple(obs['perception'].shape) == (4, 4, 27, 48)
            assert tuple(obs['proprio'].shape) == (4, 372)
            assert tuple(obs['box_pose_target'].shape) == (4, 9)
            torch.testing.assert_close(obs['amp'].reshape(4, 10, 35), task.amp_frame(b)[:, None].expand(-1, 10, -1))
            for step in range(6):
                previous = obs['amp'].reshape(4, 10, 35).clone()
                forced = step % 4
                b.episode_length_buf[forced] = b.max_episode_length - 1
                obs, rewards, dones, info = w.step(torch.zeros(4, 29, device=args.device))
                assert dones[forced]
                done_count += int(dones.sum())
                assert all(torch.isfinite(v).all() for v in obs.values()) and torch.isfinite(rewards).all()
                ids = info['terminal_observations']['env_ids']
                terminal = info['terminal_observations']['obs']['amp'].reshape(-1, 10, 35)
                torch.testing.assert_close(terminal[:, :-1], previous[ids, 1:])
                current = obs['amp'].reshape(4, 10, 35)
                torch.testing.assert_close(current[ids], current[ids, -1:].expand(-1, 10, -1))
                live = ~dones.bool()
                torch.testing.assert_close(current[live, :-1], previous[live, 1:])
            assert done_count >= 6
            w.reset()
        runner = CarryBoxWall5OnPolicyRunner(w, agent.to_dict(), log_dir=str(OUT / 'train'), device=args.device)
        original_policy = copy.deepcopy(runner.alg.policy.state_dict())
        original_d = copy.deepcopy(runner.alg.amp.state_dict())
        runner.learn(3, init_at_random_ep_len=False)
        assert runner.alg.amp_valid.all()
        assert runner.alg.amp_rollout.shape == (24, 4, 350)
        assert runner.alg.motion_library.num_clips == 15
        assert runner.alg.motion_metadata['frame_dim'] == 35
        assert runner.alg.amp_optimizer.param_groups[0]['lr'] == 5e-5
        assert not torch.equal(original_d['amp_linear.weight'], runner.alg.amp.amp_linear.weight)
        assert any(not torch.equal(original_policy[k], v) for k, v in runner.alg.policy.state_dict().items())
        assert runner.alg.optimizer.state and runner.alg.amp_optimizer.state
        assert b.extras['log']['AMP/valid_fraction'] == 1.
        logs = {k: float(v) for k, v in b.extras['log'].items() if k.startswith(('AMP/', 'Reward/'))}
        assert abs(logs['Reward/mixed_per_step'] - logs['Reward/task_weighted_per_step'] - logs['Reward/amp_per_step']) < 1e-5
        checkpoint = OUT / 'model.pt'
        runner.save(str(checkpoint))
        restored = CarryBoxWall5OnPolicyRunner(w, agent.to_dict(), log_dir=str(OUT / 'resumed'), device=args.device)
        restored.load(str(checkpoint))
        for k, v in runner.alg.amp.state_dict().items():
            torch.testing.assert_close(restored.alg.amp.state_dict()[k], v)
        restored.learn(1, init_at_random_ep_len=False)
        # Play-mode restores must keep the exact same strict identity check.
        restored.load(str(checkpoint), load_optimizer=False)
        cfg.walled_variant = 'walled4'
        for load_optimizer in (True, False):
            try:
                restored.load(str(checkpoint), load_optimizer=load_optimizer)
            except ValueError as e:
                assert 'environment' in str(e)
            else:
                raise AssertionError('Wall5 checkpoint accepted by altered environment contract')
        cfg.walled_variant = 'walled5'
        obs = w.get_observations()
        exported = export_depth_policy(restored.alg.policy, obs, str(OUT / 'export'), metadata=b.checkpoint_contract())
        with torch.inference_mode():
            expected = restored.alg.policy.act_inference(obs).cpu()
            torch.testing.assert_close(exported(obs['proprio'].cpu(), obs['perception'].cpu()), expected, atol=1e-5, rtol=1e-5)
        onnx.checker.check_model(str(OUT / 'export/policy.onnx'))
        assert all(torch.isfinite(v).all() for v in restored.alg.policy.state_dict().values())
        assert all(torch.isfinite(v).all() for v in restored.alg.amp.state_dict().values())
        report = dict(status='PASS', num_envs=4, training_iterations=3, resumed_iterations=1,
                      forced_and_natural_resets=done_count, env_differences=env_diff, runner_differences=alg_diff,
                      environment_contract=b.checkpoint_contract(), amp_contract=restored.alg.amp_config,
                      dataset=restored.alg.motion_metadata, reward_snapshot=logs,
                      jit_matches=True, onnx_checked=True, strict_restore=True,
                      formal_training_started=False, convergence='not_evaluated', timing_4096='not_measured')
        (OUT / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
        print('WALL5_SMOKE_PASS', flush=True)
    finally:
        env.close()

try:
    main()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:
    app.close(wait_for_replicator=False)
