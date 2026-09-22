"""Learning/serving regressions; production code with simulator-boundary doubles."""
import copy
import unittest
from types import SimpleNamespace
import torch
import test_soccer_v3 as fixtures
from test_agilekickball import ContinuousRoundTests, SpeedCurriculumTests
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball import AgileKickballState, exposure_speed_curriculum
from perceptual_ball.rsl_rl_extensions.ball_metrics import ball_prediction_metrics

SoccerTests = fixtures.SoccerTests


class LearningTests(unittest.TestCase):
    def algorithm(self):
        alg, obs = fixtures.make_algorithm()
        for _ in range(2):
            alg.act(obs)
            alg.process_env_step(obs, torch.zeros(4), torch.zeros(4), {})
        return alg, obs

    def test_rejected_update_reports_actual_nonzero_error(self):
        alg, _ = self.algorithm()
        before = copy.deepcopy(alg.policy.state_dict())
        alg.ball_aux_max_kl = 0.
        loss = alg._update_ball_head()
        self.assertGreater(loss, 0.)
        self.assertEqual(alg.aux_metrics['aux/encoder_updates'], 0)
        self.assertEqual(alg.aux_metrics['ball/all/count'], 8)
        for name, value in alg.policy.state_dict().items():
            torch.testing.assert_close(value, before[name])

    def test_head_fallback_updates_head_only_and_continues_batches(self):
        alg, obs = self.algorithm()
        alg.ball_aux_backtracking = True
        alg.num_mini_batches = 2
        alg.ball_aux_max_kl = 0.
        # Large trial LR makes even the smallest bounded trial violate exact-zero KL.
        alg.ball_aux_optimizer.param_groups[0]['lr'] = .1
        before_head = [p.clone() for p in alg.policy.ball_head.parameters()]
        before_encoder = [p.clone() for p in alg.policy.perception_encoder.parameters()]
        with torch.no_grad():
            actor = alg.policy.act_inference(obs).clone()
        alg._update_ball_head()
        self.assertEqual(alg.aux_metrics['aux/head_only_batches'], 2)
        self.assertTrue(any(not torch.equal(a, b) for a, b in zip(before_head, alg.policy.ball_head.parameters())))
        for a, b in zip(before_encoder, alg.policy.perception_encoder.parameters()):
            torch.testing.assert_close(a, b, rtol=0, atol=0)
        with torch.no_grad():
            torch.testing.assert_close(actor, alg.policy.act_inference(obs), rtol=0, atol=0)

    def test_backtracking_accepts_encoder_and_bounds_cumulative_kl(self):
        alg, _ = self.algorithm()
        alg.ball_aux_backtracking = True
        alg.num_mini_batches = 2
        alg._update_ball_head()
        self.assertGreater(alg.aux_metrics['aux/encoder_updates'], 0)
        self.assertLessEqual(alg.aux_metrics['aux/stage_monitor_kl'], .01 + 1.e-8)

    def test_vector_metrics_denominator_units_tail_and_empty_group(self):
        obs = fixtures.observations(5)
        obs['privileged'][:] = torch.tensor([.03, .04, 0., 0., 0., 2.])
        obs['ball_status'] = torch.zeros(5, 3)
        obs['perception'][:] = 3.
        policy = SimpleNamespace(privileged_group='privileged', predict_ball_state=lambda x: torch.zeros_like(x['privileged']))
        result = ball_prediction_metrics(policy, obs, chunk_size=2)
        self.assertEqual(result['all/count'], 5)
        self.assertAlmostEqual(result['all/position_cm_rmse'], 5., places=5)
        self.assertEqual(result['all/velocity_m_s_rmse'], 2.)
        self.assertEqual(result['active/count'], 0)
        self.assertNotIn('active/position_cm_rmse', result)

    def test_initial_reset_ignores_old_done_but_recovery_does_not(self):
        env, _ = fixtures.state_fixture()
        state = AgileKickballState(env)
        env.reset_buf[:] = True
        state.reset(torch.arange(2))
        self.assertTrue(state.ball_active.all())
        self.assertFalse(state.kick_success_flag.any())
        self.assertGreater(env.scene['ball'].data.root_lin_vel_w.norm(dim=-1).min(), .39)
        state.ball_active[:] = False
        state.wait_elapsed[:] = 1.
        state.stable_elapsed[:] = 1.
        state._serve(torch.arange(2))
        self.assertFalse(state.ball_active.any())
        self.assertEqual(state.recovered_serves.sum(), 0)

    def test_curriculum_uses_normalized_exposure_not_idle_steps(self):
        env, _ = fixtures.state_fixture()
        env._kickball = AgileKickballState(env)
        env.common_step_counter = 999999
        self.assertEqual(exposure_speed_curriculum(env, None), .8)
        env._kickball.incoming_steps[:] = 120000
        self.assertAlmostEqual(exposure_speed_curriculum(env, None), 1.4)
        env._kickball.exposure_offset = 120000
        self.assertEqual(exposure_speed_curriculum(env, None), 2.)
        self.assertEqual(env._kickball.serve_distance_range, (1.3, 2.))


if __name__ == '__main__':
    unittest.main()
