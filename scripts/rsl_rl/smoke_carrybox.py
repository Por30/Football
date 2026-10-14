"""Bounded RTX/physics/learning check, not a claim of successful task learning."""
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
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_env_cfg import CarryBoxEnvCfg, CarryBoxPPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox import box_pose_target, depth_image, hand_contacts, amp_frame
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy


def main():
    torch.set_num_threads(2)
    cfg, agent = CarryBoxEnvCfg(), CarryBoxPPORunnerCfg()
    cfg.scene.num_envs = 4; cfg.sim.device = args.device; cfg.seed = 42
    cfg.episode_length_s = .28  # includes full AMP windows, then forces timeout/reset
    agent.num_steps_per_env = 24
    agent.algorithm.num_learning_epochs = 1; agent.algorithm.num_mini_batches = 1
    env = gym.make('Template-Perceptual-Ball-CarryBox-v0', cfg=cfg)
    try:
        base = env.unwrapped
        wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        runner = CarryBoxOnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
        with torch.inference_mode():
            obs, _ = wrapped.reset()
            assert set(obs.keys()) == {'proprio', 'perception', 'box_pose_target', 'amp'}
            assert obs['proprio'].shape == (4, 372) and obs['perception'].shape == (4, 4, 32, 48)
            assert obs['amp'].shape == (4, 640)
            torch.testing.assert_close(obs['amp'].reshape(4, 10, 64)[:, -1], amp_frame(base))
            assert runner.alg.motion_library is None  # constructing play/inference doesn't need findbox
            assert torch.isfinite(obs['perception']).all() and obs['perception'].std() > .01
            torch.testing.assert_close(obs['box_pose_target'], box_pose_target(base))
            before = depth_image(base).clone()
            box = base.scene['box']
            state = box.data.root_state_w.clone(); state[:, 0] += 10.
            box.write_root_state_to_sim(state)
            base.scene.write_data_to_sim(); base.sim.forward(); base.sim.render(); base.scene.update(base.physics_dt)
            after = depth_image(base).clone()
            # Removing the box must change the actual rendered pixels, not merely the label.
            pixel_change = (before - after).abs().flatten(1).amax(-1)
            assert (pixel_change > .01).all(), ('camera does not see box', pixel_change)
            obs, _ = wrapped.reset()
            torch.testing.assert_close(obs['perception'][:, -1], depth_image(base))
            torch.testing.assert_close(obs['box_pose_target'], box_pose_target(base))
            for side in ('left', 'right'):
                sensor = base.scene[f'{side}_box_contact']
                assert sensor.data.force_matrix_w.shape == (4, 1, 1, 3)
            assert hand_contacts(base).shape == (4, 2)
            contact_forces = {}
            # Deliberately overlap each physical hand with the box, separately, to verify
            # that the filter is connected to colliding geometry (shape alone is insufficient).
            for side in ('left', 'right'):
                wrapped.reset()
                hand = base.scene['robot'].find_bodies(f'{side}_rubber_hand')[0][0]
                state = box.data.root_state_w.clone()
                state[:, :3] = base.scene['robot'].data.body_pos_w[:, hand]
                state[:, 3:7] = torch.tensor([1., 0., 0., 0.], device=args.device)
                state[:, 7:] = 0.
                box.write_root_state_to_sim(state)
                base.scene.write_data_to_sim()
                base.sim.step(render=True)
                base.scene.update(base.physics_dt)
                force = base.scene[f'{side}_box_contact'].data.force_matrix_w.norm(dim=-1).amax()
                assert force > 1., ('hand/box contact filter is disconnected', side, force)
                contact_forces[side] = float(force)
            obs, _ = wrapped.reset()
        losses, timeouts = [], 0
        for iteration in range(2):
            amp_before = copy.deepcopy(runner.alg.amp.state_dict())
            with torch.inference_mode():
                for _ in range(agent.num_steps_per_env):
                    action = runner.alg.act(obs)
                    obs, reward, done, extras = wrapped.step(action)
                    assert torch.isfinite(reward).all()
                    timeouts += int(extras['time_outs'].sum())
                    runner.alg.process_env_step(obs, reward, done, extras)
                    index = runner.alg.storage.step - 1
                    if done.any():
                        terminal = extras['terminal_observations']
                        ids = terminal['env_ids']
                        torch.testing.assert_close(runner.alg.amp_rollout[index, ids], terminal['obs']['amp'])
                        fresh = obs['amp'][ids].reshape(len(ids), 10, 64)
                        torch.testing.assert_close(fresh, fresh[:, -1:].expand_as(fresh))
                runner.alg.compute_returns(obs)
            result = runner.alg.update()
            assert all(torch.isfinite(torch.tensor(v)) for v in result.values())
            assert result['amp_valid_samples'] > 0
            assert not torch.equal(amp_before['amp_linear.weight'], runner.alg.amp.amp_linear.weight)
            losses.append(result)
        assert timeouts > 0
        before = copy.deepcopy(runner.alg.policy.state_dict())
        amp_before = copy.deepcopy(runner.alg.amp.state_dict())
        out = Path('docs/carrybox'); out.mkdir(exist_ok=True, parents=True)
        runner.save(str(out / 'smoke_model.pt'))
        runner.load(str(out / 'smoke_model.pt'))
        for key, value in runner.alg.policy.state_dict().items(): torch.testing.assert_close(value, before[key])
        for key, value in runner.alg.amp.state_dict().items(): torch.testing.assert_close(value, amp_before[key])
        assert runner.alg.optimizer.state and runner.alg.amp_optimizer.state
        assert runner.alg.motion_metadata['clip_count'] == 17
        assert runner.alg.motion_library is None
        with torch.inference_mode():
            deployment = {key: obs[key] for key in ('proprio', 'perception')}
            assert torch.isfinite(runner.alg.policy.act_inference(deployment)).all()
            assert torch.isfinite(runner.alg.policy.evaluate(deployment)).all()
        wrapper = export_depth_policy(runner.alg.policy, obs, out / 'exported')
        with torch.no_grad():
            torch.testing.assert_close(wrapper(obs['proprio'].cpu(), obs['perception'].cpu()),
                                       runner.alg.policy.act_inference(obs).cpu(), atol=1.e-5, rtol=1.e-5)
        summary = dict(status='PASS', envs=4, updates=2, timeout_transitions=timeouts,
                       depth_pixel_change=pixel_change.tolist(), losses=losses,
                       hand_bodies=base.scene['robot'].find_bodies(['left_rubber_hand', 'right_rubber_hand'])[1],
                       forced_hand_contact_newtons=contact_forces,
                       amp_dataset=runner.alg.motion_metadata, amp_observation_dim=640,
                       checkpoint_and_export=True, trained_pickup_success='not_evaluated')
        (out / 'smoke.json').write_text(json.dumps(summary, indent=2)+'\n')
        print('CARRYBOX_SMOKE_PASS', json.dumps(summary))
    finally:
        env.close()


try:
    main()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:
    app.close()
