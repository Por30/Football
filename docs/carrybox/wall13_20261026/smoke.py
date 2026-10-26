"""Verify wall13 data identity, unchanged behavior, PPO/AMP/aux update and resume."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import copy
import hashlib
import json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab_tasks.utils import load_cfg_from_registry
from perceptual_ball.carrybox_amp import DEFAULT_DATASET_PATH
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall12_env_cfg import CarryBoxWalled12EnvCfg, CarryBoxWalled12PPORunnerCfg
from perceptual_ball.rsl_rl_extensions.carrybox_wall12 import CarryBoxWall12OnPolicyRunner

OUT = Path(__file__).resolve().parent
WALL12 = Path('logs/rsl_rl/g1_carrybox_depth/walled12/2026-10-25_12-32-53_wall12_24step_pose_aux_fresh_20261025_123249/model_19999.pt')


def differences(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        return [p for k in a.keys() | b.keys() for p in differences(a.get(k), b.get(k), path+'.'+k)]
    return [] if a == b else [path.lstrip('.')]


def main():
    torch.set_num_threads(2)
    task_id = 'Template-Perceptual-Ball-CarryBox-Walled13-v0'
    cfg = load_cfg_from_registry(task_id, 'env_cfg_entry_point')
    agent = load_cfg_from_registry(task_id, 'rsl_rl_cfg_entry_point')
    env_diff = differences(cfg.to_dict(), CarryBoxWalled12EnvCfg().to_dict())
    runner_diff = differences(agent.to_dict(), CarryBoxWalled12PPORunnerCfg().to_dict())
    assert env_diff == ['walled_variant'], env_diff
    assert set(runner_diff) == {'experiment_name', 'run_name'}, runner_diff
    assert agent.algorithm.amp_data_dir == DEFAULT_DATASET_PATH
    assert (cfg.scene.num_envs, agent.num_steps_per_env, agent.algorithm.num_learning_epochs,
            agent.algorithm.num_mini_batches, agent.algorithm.pose_aux_coef) == (4096, 24, 5, 4, 1.)
    root = Path(agent.algorithm.amp_data_dir)
    manifest_bytes = (root/'amp_manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    assert manifest['dataset_revision'] == 3 and manifest['dataset_version'] == 'findbox_hold_v1_named'
    assert len(manifest['clips']) == 15 and sum(r['frames'] for r in manifest['clips']) == 4155
    for row in manifest['clips']:
        assert hashlib.sha256((root/row['file']).read_bytes()).hexdigest() == row['sha256']
    hold = torch.load(root/'hold/hold_box_01.pt', weights_only=True, map_location='cpu')
    for name, value in hold.items():
        if isinstance(value, torch.Tensor) and value.ndim and len(value) == 300:
            torch.testing.assert_close(value[20:], value[20:21].expand_as(value[20:]), atol=0, rtol=0)
    for name in ('base_linear_velocity', 'base_angular_velocity', 'joint_velocity'):
        assert (hold[name][20:] == 0).all(), name
    old = torch.load(WALL12, weights_only=False, map_location='cpu')
    assert old['amp']['dataset']['manifest_sha256'] == manifest_hash
    cfg.scene.num_envs = 16
    cfg.seed = 42
    cfg.sim.device = args.device
    for name in ('gpu_found_lost_pairs_capacity', 'gpu_found_lost_aggregate_pairs_capacity', 'gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx, name, 262144)
    env = gym.make(task_id, cfg=cfg)
    try:
        wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        obs, _ = wrapped.reset()
        expected = {'proprio': [16, 558], 'perception': [16, 4, 27, 48], 'critic_state': [16, 123],
                    'box_pose_target': [16, 12], 'amp': [16, 600]}
        assert {k: list(v.shape) for k, v in obs.items()} == expected
        runner = CarryBoxWall12OnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
        initial = copy.deepcopy(runner.alg.policy.state_dict())
        initial_amp = copy.deepcopy(runner.alg.amp.state_dict())
        with torch.inference_mode():
            for step in range(24):
                if step == 0:
                    env.unwrapped.episode_length_buf[0] = env.unwrapped.max_episode_length - 1
                obs, rewards, dones, extra = wrapped.step(runner.alg.act(obs))
                assert torch.isfinite(rewards).all() and all(torch.isfinite(v).all() for v in obs.values())
                if step == 0:
                    assert dones[0] and any(k.startswith('Wall13/') for k in extra['log'])
                    assert not any(k.startswith(('Wall10/', 'Wall11/', 'Wall12/')) for k in extra['log'])
                runner.alg.process_env_step(obs, rewards, dones, extra)
            runner.alg.compute_returns(obs)
        losses = runner.alg.update()
        assert all(torch.isfinite(torch.tensor(v)) for v in losses.values())
        assert losses['pose_samples'] == 16 * 23 * 5
        for prefix in ('actor.', 'critic.', 'perception_encoder.', 'pose_head.'):
            assert any(not torch.equal(v, initial[k]) for k, v in runner.alg.policy.state_dict().items() if k.startswith(prefix))
        assert any(not torch.equal(v, initial_amp[k]) for k, v in runner.alg.amp.state_dict().items())
        assert runner.alg.motion_metadata == old['amp']['dataset']
        library = runner.alg.motion_library
        hold_id = library.clip_names.index('hold/hold_box_01.pt')
        ids = torch.tensor([hold_id], device=args.device)
        window = library.windows(ids, torch.tensor([40.], device=args.device)).reshape(1, 10, 60)
        torch.testing.assert_close(window, window[:, :1].expand_as(window), atol=1.e-6, rtol=1.e-6)
        runner.current_learning_iteration = 1
        runner.save(OUT/'smoke_model.pt')
        restored = CarryBoxWall12OnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
        restored.load(OUT/'smoke_model.pt')
        with torch.inference_mode():
            torch.testing.assert_close(restored.alg.policy.act_inference(obs), runner.alg.policy.act_inference(obs), atol=0, rtol=0)
            torch.testing.assert_close(restored.alg.policy.predict_box_pose(obs), runner.alg.policy.predict_box_pose(obs), atol=0, rtol=0)
        assert all(p in restored.alg.optimizer.state for p in restored.alg.policy.pose_head.parameters())
        assert {int(s['step']) for s in restored.alg.optimizer.state.values()} == {20}
        contract = env.unwrapped.checkpoint_contract()
        assert contract['variant'] == 'walled13' and contract['parent'] == 'walled12_revision1'
        try:
            restored.load(WALL12)
        except ValueError as error:
            assert 'environment variant/contract' in str(error)
        else:
            raise AssertionError('Wall12 checkpoint accepted as wall13')
        (OUT/'smoke.json').write_text(json.dumps(dict(status='PASS', num_envs=16, rollout_steps=24,
            updates=20, shapes=expected, env_differences=env_diff, runner_differences=runner_diff,
            dataset_path=str(root), manifest_sha256=manifest_hash, dataset=runner.alg.motion_metadata,
            identical_to_wall12_dataset=True, hold_frames=300, stationary_from_frame=20,
            stationary_expert_window=True, losses=losses, contract=contract,
            strict_resume=True, wall12_strict_resume_rejected=True,
            formal_training_started=False), indent=2)+'\n')
        print('WALL13_SMOKE_PASS', flush=True)
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
