"""Kickball v11 learning and return contracts; simulator doubles only at the boundary."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
import torch
from tensordict import TensorDict
import test_carrybox as fixtures
from test_agilekickball_v4 import V4Tests
from test_agilekickball_v3 import V3Tests
from perceptual_ball.kickball_v11 import KickMotionLibrary, KickballV11State, ball_state_loss
from perceptual_ball.rsl_rl_extensions.kickball_v11 import (
    KickballV11ActorCritic, KickballV11PPO, KickballV11OnPolicyRunner)
from perceptual_ball.rsl_rl_extensions.export import DepthPolicyExport


def algorithm():
    obs = TensorDict(dict(proprio=torch.randn(4, 558) * .05, perception=torch.rand(4, 4, 27, 48),
        critic_state=torch.randn(4, 124) * .05, ball_target=torch.randn(4, 6), amp=torch.zeros(4, 600)), [4])
    policy = KickballV11ActorCritic(obs, {'policy': ['proprio', 'perception'], 'critic': ['critic_state']},
                                   29, actor_hidden_dims=(32,), critic_hidden_dims=(32,))
    from perceptual_ball.kickball_v11 import MOTION_DIR
    alg = KickballV11PPO(policy, device='cpu', amp_coef=.25, amp_reward_scale=.5, pose_aux_coef=1.,
        amp_data_dir=MOTION_DIR, num_learning_epochs=1, num_mini_batches=1,
        learning_rate=.001, schedule='adaptive')
    alg.init_storage('rl', 4, 4, obs, [29])
    return alg, obs


def runner(alg, env, kb):
    result = KickballV11OnPolicyRunner.__new__(KickballV11OnPolicyRunner)
    result.alg, result.device, result.current_learning_iteration = alg, 'cpu', 2
    env.checkpoint_contract = lambda: dict(variant='kickballv11', critic=124)
    result.env = NS(unwrapped=env, reset=lambda: kb.reset(torch.arange(env.num_envs)))
    return result


class V11StateTests(V4Tests):
    # Inherit the v4 hit, failure, accounting and direction-course regressions.
    def state(self, n=2):
        env, _ = V3Tests().state(n)
        kb = KickballV11State(env)
        env._kickball = kb
        kb.reset(torch.arange(n))
        kb._window_counts = kb._counts()
        return env, kb

    def test_v3_full_initialization_and_preflight(self):
        # V4 supports this migration; v11 has a new network and must reject it.
        with self.assertRaisesRegex(ValueError, 'fresh v4 state feedback runner'):
            super().test_v3_full_initialization_and_preflight()

    def test_speed_cap_override_and_curriculum_restore(self):
        env, kb = self.state()
        self.assertEqual(kb.rsi_probability, 0.)
        self.assertEqual(kb.serve_distance_range, (1.3, 2.))
        self.assertAlmostEqual(kb.serve_speed_range[1], 1.1)
        kb.extension_unlocked = True
        kb.extension_start_upper = 1.1
        kb.extension_steps = kb.course_config['extension_steps']
        kb.direction_steps = 120000.
        kb._sync_course()
        self.assertEqual(kb.serve_speed_range, (.4, 5.))
        self.assertAlmostEqual(kb.target_half_width, .2)
        saved = kb.curriculum_state_dict()
        _, restored = self.state()
        restored.load_curriculum_state_dict(saved)
        self.assertEqual(restored.curriculum_state_dict(), saved)
        restored.serve_speed_override = (5., 5.)
        self.assertTrue((restored._sample_serve_speed(torch.arange(2)) == 5.).all())
        restored.serve_speed_override = (5.1, 5.1)
        with self.assertRaisesRegex(ValueError, '0.4--5'):
            restored._sample_serve_speed(torch.arange(2))


class V11LearningTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)

    def test_native_kick_features_windows_and_zero_object(self):
        lib = KickMotionLibrary()
        self.assertEqual(lib.lengths.tolist(), [498, 589])
        self.assertAlmostEqual(lib.fps, 120., places=3)
        self.assertEqual(len(lib.metadata['files']), 2)
        self.assertEqual(len(lib.joint_names), 29)
        self.assertEqual(lib.joint_names[:2], ['left_hip_pitch_joint', 'right_hip_pitch_joint'])
        x, ids = lib.sample_expert_amp_obs(1024, return_clip_ids=True)
        self.assertTrue(torch.isfinite(x).all())
        self.assertTrue((x.reshape(-1, 60)[:, 57:] == 0).all())
        self.assertEqual(set(ids.tolist()), {0, 1})
        torch.testing.assert_close(lib.windows(torch.arange(2), torch.zeros(2)).reshape(2, 10, 60)[:, 0],
                                   lib.frames[lib.offsets])
        with self.assertRaisesRegex(ValueError, 'boundary'):
            lib.windows(torch.arange(2), lib.lengths.float() - 1)
        # Compare to the original football loader, including native interpolation.
        from perceptual_ball.amp_features import pack_amp_frame
        i = 30
        expected = pack_amp_frame(lib.base_height[i], lib.joint_position[i], lib.ee_pos_b[i],
                                  lib.base_lin_vel_b[i], lib.base_ang_vel_b[i], lib.root_rot_6d[i])
        torch.testing.assert_close(lib.frames[i], expected)

    def test_auxiliary_gradient_privilege_boundary_and_export(self):
        alg, obs = algorithm()
        model = alg.policy
        action = model.act_inference(obs).detach()
        other = obs.clone()
        for key in ('critic_state', 'amp', 'ball_target'):
            other[key] += 1000.
        torch.testing.assert_close(model.act_inference(other), action, atol=0, rtol=0)
        self.assertFalse(torch.equal(model.evaluate(other), model.evaluate(obs)))
        model.evaluate(obs).sum().backward()
        self.assertTrue(all(p.grad is None for p in model.perception_encoder.parameters()))
        model.zero_grad(set_to_none=True)
        target = obs['ball_target'].clone().requires_grad_()
        sum(ball_state_loss(model.predict_ball(obs), target)).backward()
        self.assertIsNone(target.grad)
        for module in (model.perception_encoder, model.ball_head):
            self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in module.parameters()))
            self.assertGreater(sum(float(p.grad.abs().sum()) for p in module.parameters()), 0.)
        self.assertTrue(all(p.grad is None for p in model.critic.parameters()))
        self.assertTrue(all(p.grad is None for p in model.actor.parameters()))
        exported = torch.jit.script(DepthPolicyExport(model, obs))
        torch.testing.assert_close(exported(obs['proprio'], obs['perception']), action)
        self.assertFalse(any('ball_head' in k or 'critic' in k for k in exported.state_dict()))
        with self.assertRaises(ValueError):
            ball_state_loss(torch.zeros(4, 6), torch.zeros(4, 9))

    def test_joint_update_auxiliary_and_full_checkpoint(self):
        alg, obs = algorithm()
        before = copy.deepcopy(alg.policy.state_dict())
        amp_before = alg.amp.amp_linear.weight.detach().clone()
        with torch.inference_mode():
            for i in range(4):
                alg.act(obs)
                next_obs = obs.clone()
                next_obs['ball_target'] += 100.  # Current labels must not shift to next obs.
                next_obs['amp'] = alg.motion_library.sample_expert_amp_obs(4) if alg.motion_library else obs['amp']
                done = torch.tensor([i == 0, False, False, False])
                terminal = {k:v[:1].clone() for k,v in next_obs.items()}
                if done[0]:
                    next_obs['amp'][0] = 999.
                extra = {'terminal_observations': {'env_ids': torch.tensor([0]), 'obs': terminal}}
                alg.process_env_step(next_obs, torch.ones(4), done, extra)
                torch.testing.assert_close(alg.storage.observations['ball_target'][i], obs['ball_target'])
                if done[0]:
                    torch.testing.assert_close(alg.amp_rollout[i,0], terminal['amp'][0])
                obs = next_obs
            alg.compute_returns(obs)
        losses = alg.update()
        self.assertTrue(all(torch.isfinite(torch.tensor(v)) for v in losses.values()))
        for prefix in ('actor.', 'critic.', 'perception_encoder.', 'ball_head.'):
            self.assertTrue(any(not torch.equal(before[k], v) for k,v in alg.policy.state_dict().items()
                                if k.startswith(prefix)), prefix)
        self.assertFalse(torch.equal(amp_before, alg.amp.amp_linear.weight))
        self.assertIs(alg.optimizer, alg.amp_optimizer)
        self.assertEqual({int(s['step']) for s in alg.optimizer.state.values()}, {1})
        env, kb = V11StateTests().state(4)
        kb.extension_unlocked = True
        kb.extension_steps = 10000.
        kb.direction_steps = 5000.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'model.pt'
            runner(alg, env, kb).save(path)
            fresh, _ = algorithm()
            fresh_env, fresh_kb = V11StateTests().state(4)
            restored = runner(fresh, fresh_env, fresh_kb)
            restored.load(path)
            self.assertEqual(fresh_kb.curriculum_state_dict(), kb.curriculum_state_dict())
            with torch.inference_mode():
                torch.testing.assert_close(fresh.policy.act_inference(obs), alg.policy.act_inference(obs), atol=0, rtol=0)
            restored.load(path, load_optimizer=False)
            self.assertFalse(fresh_kb.curriculum_training)
            data = torch.load(path, weights_only=False)
            data['kickball_v11_curriculum']['config']['speed_bounds'][-1] = 6.
            torch.save(data, path)
            with self.assertRaises(ValueError):
                restored.load(path)
            data.pop('kickball_v11_schema')
            torch.save(data, path)
            with self.assertRaisesRegex(ValueError, 'Not a kickballv11'):
                restored.load(path)


if __name__ == '__main__':
    unittest.main()
