"""Sender-plane semantics, round accounting and complete stable-v3 initialization."""
import copy
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import unittest
import torch
import test_agilekickball_v3 as previous
import test_state_feedback as feedback
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v4 import (
    AgileKickballV4State, RETURN_CONFIG, return_quality, source_gate_crossing)
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner


class V4Tests(unittest.TestCase):
    tick = previous.V3Tests.tick

    def state(self, n=2):
        env, _ = previous.V3Tests().state(n)
        kb = AgileKickballV4State(env)
        env._kickball = kb
        kb.reset(torch.arange(n))
        kb._window_counts = kb._counts()
        return env, kb

    def arrange_kick(self, env, kb, y=0., speed=2.):
        kb.source_xy[:] = torch.tensor([1.5, 0.])
        kb.return_normal[:] = torch.tensor([1., 0.])
        kb.previous_ball_xyz[:] = torch.tensor([.22, 0., .11])
        kb.prev_ball_vel_xy[:] = torch.tensor([-1., 0.])
        env.scene['ball'].data.root_pos_w[:] = torch.tensor([.2, 0., .11])
        env.scene['ball'].data.root_lin_vel_w[:] = torch.tensor([speed, y, 0.])

    def cross(self, env, kb, y=0., x=1.7):
        kb.previous_ball_xyz[:] = torch.tensor([1.3, y, .11])
        env.scene['ball'].data.root_pos_w[:] = torch.tensor([x, y, .11])
        env.scene['ball'].data.root_lin_vel_w[:] = torch.tensor([6., 0., 0.])
        self.tick(env, kb)

    def test_serve_sampling_subset_reset_and_recovery(self):
        env, kb = self.state()
        torch.testing.assert_close(kb.source_xy, env.scene['ball'].data.root_pos_w[:, :2])
        velocity = env.scene['ball'].data.root_lin_vel_w[:, :2]
        torch.testing.assert_close(kb.return_normal, -velocity / velocity.norm(dim=-1, keepdim=True))
        before = kb.source_xy.clone()
        kb.ball_active[:] = False
        kb.wait_elapsed[:] = torch.tensor([1., 0.])
        kb.stable_elapsed[:] = torch.tensor([1., 0.])
        kb._serve(torch.arange(2))
        self.assertEqual(kb.recovered_serves.tolist(), [1, 0])
        torch.testing.assert_close(kb.source_xy[1], before[1])
        self.assertTrue(kb.round_open.all())
        # Reset only one environment: finish that old round and clear its eligibility.
        kb.return_has_strike[:] = True
        kb.reset(torch.tensor([0]))
        self.assertEqual(kb.completed_rounds.tolist(), [1, 0])
        self.assertEqual(kb.return_has_strike.tolist(), [False, True])

    def test_single_success_reentry_completed_denominator_and_no_leak(self):
        env, kb = self.state()
        self.arrange_kick(env, kb)
        self.tick(env, kb)
        self.assertTrue(kb.return_has_strike.all())
        self.assertTrue((kb.return_kick_quality > .99).all())
        self.assertTrue((kb.return_dense > 0).all())
        self.cross(env, kb)
        self.assertEqual(kb.target_hits.tolist(), [1, 1])
        self.assertEqual(kb.strict_hits.tolist(), [1, 1])
        self.assertEqual(kb.completed_rounds.sum().item(), 0)
        kb.tick()
        self.assertEqual(kb.target_hits.tolist(), [1, 1])
        self.cross(env, kb)
        self.assertFalse(kb.return_target_pulse.any())
        self.assertFalse(kb.return_dense.any())
        env.scene['ball'].data.root_pos_w[:, 0] = 3.1
        self.tick(env, kb)
        self.assertEqual(kb.completed_rounds.tolist(), [1, 1])
        self.assertEqual(kb.completed_strict_hits.tolist(), [1, 1])
        self.assertFalse(kb.return_miss_pulse.any())
        self.tick(env, kb, 22)
        self.assertTrue(kb.ball_active.all())
        self.assertFalse(kb.return_hit.any())
        self.assertFalse(kb.return_has_strike.any())
        self.assertFalse(kb.return_dense.any())
        torch.testing.assert_close(kb.source_xy, env.scene['ball'].data.root_pos_w[:, :2])

    def test_no_incoming_body_sideways_backwards_or_terminal_success(self):
        for mode in ('incoming', 'body', 'sideways', 'backwards', 'terminal', 'slow'):
            with self.subTest(mode=mode):
                env, kb = self.state()
                self.arrange_kick(env, kb)
                if mode == 'body':
                    env.scene['robot'].data.body_link_pos_w[:] = 2.
                if mode == 'terminal':
                    env.reset_buf[:] = True
                if mode == 'incoming':
                    env.scene['ball'].data.root_pos_w[:, 0] = 1.4
                    env.scene['ball'].data.root_lin_vel_w[:, 0] = -1.
                if mode in ('sideways', 'backwards', 'slow'):
                    env.scene['ball'].data.root_lin_vel_w[:] = torch.tensor(
                        [0., 2., 0.] if mode == 'sideways' else [-2., 0., 0.] if mode == 'backwards' else [.2, 0., 0.])
                self.tick(env, kb)
                self.assertFalse(kb.return_dense.any())
                self.assertFalse(kb.return_target_pulse.any())
                if mode in ('incoming', 'body', 'terminal'):
                    self.cross(env, kb)
                    self.assertFalse(kb.return_target_pulse.any())

    def test_gate_miss_current_width_fixed_strict_width_and_end_same_step(self):
        env, kb = self.state()
        self.arrange_kick(env, kb); self.tick(env, kb)
        self.cross(env, kb, y=.4)
        self.assertTrue(kb.return_hit.all()); self.assertFalse(kb.strict_return_hit.any())
        env, kb = self.state()
        self.arrange_kick(env, kb); self.tick(env, kb)
        self.cross(env, kb, y=.8)
        self.assertFalse(kb.return_hit.any())
        env, kb = self.state()
        self.arrange_kick(env, kb); self.tick(env, kb)
        self.cross(env, kb, x=3.1)
        self.assertFalse(kb.ball_active.any())
        self.assertTrue(kb.return_target_pulse.all())
        self.assertEqual(kb.completed_strict_hits.tolist(), [1, 1])
        # Reset of an unfinished miss is in the denominator exactly once.
        kb.reset(torch.arange(2)); kb.reset(torch.arange(2))
        self.assertEqual(kb.completed_rounds.tolist(), [2, 2])

    def test_reward_quality_finite_monotonic_window_and_single_round_bound(self):
        xy = torch.zeros(5, 2)
        source = torch.tensor([[1.5, 0.]]).repeat(5, 1)
        normal = torch.tensor([[1., 0.]]).repeat(5, 1)
        velocity = torch.tensor([[2., 0.], [2., .4], [2., 2.], [-2., 0.], [float('nan'), 0.]])
        quality, speed, _ = return_quality(xy, velocity, source, normal, torch.full((5,), .2))
        self.assertTrue(torch.isfinite(quality).all() and torch.isfinite(speed).all())
        self.assertTrue(quality[0] > quality[1] > quality[2])
        self.assertEqual(quality[3:].tolist(), [0., 0.])
        env, kb = self.state()
        self.arrange_kick(env, kb); self.tick(env, kb)
        total = kb.return_dense.clone()
        for _ in range(40):
            self.tick(env, kb); total += kb.return_dense
        self.assertFalse(kb.return_dense.any())
        self.assertTrue((total * env.step_dt <= RETURN_CONFIG['shaping_duration_s'] + 1.e-6).all())
        self.assertFalse(kb.return_kick_quality.any())

    def test_rotated_gate_high_speed_reverse_height_and_parallel(self):
        prev = torch.tensor([[0., .8, .11], [0., 1.2, .11], [.3, .8, .11], [0., .8, 1.], [0., .8, .11]])
        curr = torch.tensor([[0., 1.2, .11], [0., .8, .11], [.3, 1.2, .11], [0., 1.2, 1.], [.4, .8, .11]])
        source = torch.tensor([[0., 1.]]).repeat(5, 1)
        normal = torch.tensor([[0., 1.]]).repeat(5, 1)
        hit, _, _ = source_gate_crossing(prev, curr, source, normal, torch.full((5,), .2))
        self.assertEqual(hit.tolist(), [True, False, False, False, False])

    def test_direction_course_gates_round_freeze_and_checkpoint(self):
        env, kb = self.state()
        initial = kb.round_half_width.clone()
        def window(hits=160, recovery=.9):
            kb.completed_rounds[0] += 200; kb.completed_target_hits[0] += hits
            kb.serves[0] += 200; kb.recovered_serves[0] += int(200 * recovery); kb.successes[0] += 180
            env.common_step_counter += 6000; kb._sync_course()
        window(hits=0)
        self.assertEqual(kb.direction_advance_rate, 0)
        window()
        self.assertEqual(kb.direction_advance_rate, 1)
        window()
        self.assertLess(kb.target_half_width, .6)
        torch.testing.assert_close(initial, kb.round_half_width)
        window(recovery=.4)
        self.assertEqual(kb.direction_advance_rate, 0)
        before = kb.direction_steps; window(recovery=.4)
        self.assertEqual(kb.direction_steps, before)
        for _ in range(23): window()
        self.assertAlmostEqual(kb.target_half_width, .2)
        saved = kb.curriculum_state_dict()
        _, restored = self.state(1); restored.load_curriculum_state_dict(saved)
        self.assertEqual(restored.curriculum_state_dict(), saved)
        restored.curriculum_training = False
        restored.env.common_step_counter += 24000; restored._sync_course()
        self.assertEqual(restored.curriculum_state_dict(), saved)
        with self.assertRaises(ValueError): previous.V3Tests().state()[1].load_curriculum_state_dict(saved)
        for value in (float('nan'), -1, 120001, True):
            bad = copy.deepcopy(saved); bad['return_direction']['steps'] = value
            with self.assertRaises(ValueError): restored.load_curriculum_state_dict(bad)

    def test_v3_full_initialization_and_preflight(self):
        source_alg, obs = feedback.algorithm(stable=True)
        with torch.no_grad(): source_alg.policy.actor.residual[-1].bias.fill_(.4)
        target_alg, _ = feedback.algorithm(stable=True)
        env, kb = self.state(4)
        runner = BallRegressionOnPolicyRunner.__new__(BallRegressionOnPolicyRunner)
        runner.alg, runner.device, runner.env = target_alg, 'cpu', SimpleNamespace(unwrapped=env)
        runner.current_learning_iteration = 0
        source = dict(soccer_schema_version=3, iter=49999,
            agile_v3_state_feedback_curriculum=previous.V3Tests().state()[1].curriculum_state_dict(),
            state_feedback=dict(config=source_alg.state_feedback_config, aux_updates=200000),
            model_state_dict=source_alg.policy.state_dict(), amp_state_dict=None)
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / 'v3.pt')
            for kind in ('revision', 'shape', 'nan', 'feedback'):
                bad = copy.deepcopy(source)
                if kind == 'revision': bad['agile_v3_state_feedback_curriculum']['config']['revision'] = 'old'
                if kind == 'shape': bad['model_state_dict']['actor.residual.4.bias'] = torch.zeros(1)
                if kind == 'nan': bad['model_state_dict']['actor.residual.4.bias'][0] = float('nan')
                if kind == 'feedback': bad['state_feedback']['config'] = {}
                torch.save(bad, path)
                with patch.object(runner.alg.policy, 'load_state_dict') as loader:
                    with self.assertRaises(ValueError): runner.warm_start_from_v3(path)
                    loader.assert_not_called()
            torch.save(source, path)
            runner.warm_start_from_v3(path)
            for name, value in source_alg.policy.state_dict().items():
                torch.testing.assert_close(target_alg.policy.state_dict()[name], value, rtol=0, atol=0)
            with torch.no_grad():
                torch.testing.assert_close(target_alg.policy.act_inference(obs), source_alg.policy.act_inference(obs), rtol=0, atol=0)
                torch.testing.assert_close(target_alg.policy.evaluate(obs), source_alg.policy.evaluate(obs), rtol=0, atol=0)
            self.assertFalse(target_alg.optimizer.state or target_alg.ball_aux_optimizer.state)
            self.assertEqual(target_alg.state_feedback_updates, 0)
            self.assertEqual(kb.course_steps, 0)
            with patch.object(runner.alg.policy, 'load_state_dict') as loader:
                with self.assertRaisesRegex(ValueError, 'v4 return curriculum'): runner.load(path)
                loader.assert_not_called()


def load_tests(loader, tests, pattern):
    tests.addTests(loader.loadTestsFromModule(previous))
    return tests


if __name__ == '__main__': unittest.main()
