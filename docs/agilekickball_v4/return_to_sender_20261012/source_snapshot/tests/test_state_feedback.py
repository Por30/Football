"""Feedback distribution, information flow, rollback, export and checkpoint tests."""
import contextlib
import copy
import io
import math
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import torch
import test_soccer_v3 as fixtures
from perceptual_ball.rsl_rl_extensions.state_feedback import (
    StateFeedbackActorCritic, StateFeedbackPPO, append_ball_feedback)
from perceptual_ball.rsl_rl_extensions.modules import PerceptionActorCritic
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy


def algorithm(stable=False):
    obs = fixtures.observations(4)
    obs['ball_status'] = torch.ones(4, 3)
    policy_settings = dict(feedback_logstd_min=-2., feedback_smooth_std=True, feedback_residual_limit=.1) if stable else {}
    with contextlib.redirect_stdout(io.StringIO()):
        policy = StateFeedbackActorCritic(obs,
            {'policy': ['proprio_hist', 'perception'], 'critic': ['proprio', 'robot_vel', 'privileged']},
            29, actor_hidden_dims=(32,), critic_hidden_dims=(32,), critic_obs_normalization=False, **policy_settings)
    alg = StateFeedbackPPO(policy, device='cpu', num_learning_epochs=1,
                          num_mini_batches=2, ball_aux_backtracking=True, ball_aux_epochs=1,
                          ball_aux_update_encoder=not stable, ball_aux_lr=1.e-4 if stable else 1.e-3,
                          ball_aux_max_kl=1.e-3 if stable else 1.e-2)
    alg.init_storage('rl', 4, 4, obs, [29])
    return alg, obs


def collect(alg, obs):
    with torch.inference_mode():
        for _ in range(4):
            alg.act(obs)
            alg.process_env_step(obs, torch.arange(4).float() * .1, torch.zeros(4), {})
        alg.compute_returns(obs)


def fixed_head(policy, values):
    with torch.no_grad():
        for p in policy.ball_head.parameters():
            p.zero_()
        policy.ball_head[-1].bias.copy_(torch.tensor(values))


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)

    def test_normalization_nll_and_physical_output(self):
        alg, obs = algorithm()
        fixed_head(alg.policy, [0.] * 12)
        obs['privileged'][:] = torch.tensor([3., 3., 3., 6., 6., 6.])
        self.assertAlmostEqual(alg.policy.ball_nll(obs).item(), .5, places=6)
        fixed_head(alg.policy, [1.] * 6 + [0.] * 6)
        torch.testing.assert_close(alg.policy.predict_ball_state(obs), obs['privileged'])
        self.assertEqual(alg.policy.ball_nll(obs).item(), 0.)
        fixed_head(alg.policy, [1.] * 6 + [math.log(.5)] * 6)
        self.assertAlmostEqual(alg.policy.ball_nll(obs).item(), math.log(.5), places=6)
        fixed_head(alg.policy, [0.] * 6 + [-99., 99., 0., -99., 99., 0.])
        _, logstd = alg.policy.ball_distribution(obs)
        torch.testing.assert_close(logstd[0], torch.tensor([-4., 1., 0., -4., 1., 0.]))

    def test_gate_visibility_recency_uncertainty_and_detach(self):
        raw = torch.zeros(4, 992)
        depth = torch.full((4, 8, 27, 48), 3.)
        depth[1, 0, 1, 1] = .5
        depth[2:, -1, 1, 1] = .5
        distribution = torch.zeros(4, 12, requires_grad=True)
        with torch.no_grad():
            distribution[3, 6:] = 1.
        features = append_ball_feedback(raw, depth, distribution)
        gate = features[:, -1]
        torch.testing.assert_close(gate, torch.tensor([0., .8**7 / 2., .5, 1/(1+math.e)]))
        self.assertFalse(features.requires_grad)
        depth[:] = .05  # nearer than sensor near limit is not a ball pixel
        self.assertEqual(append_ball_feedback(raw, depth, distribution)[:, -1].sum(), 0.)

    def test_initial_base_equivalence_nonzero_branch_and_bound(self):
        alg, obs = algorithm()
        policy = alg.policy
        raw = PerceptionActorCritic._actor_features(policy, obs)
        torch.testing.assert_close(policy.act_inference(obs), policy.actor.base(raw), rtol=0, atol=0)
        with torch.no_grad():
            policy.actor.residual[-1].bias.fill_(100.)
        delta = policy.act_inference(obs) - policy.actor.base(raw)
        self.assertGreater(delta.abs().mean(), .01)
        self.assertLessEqual(delta.abs().max(), .25 + 1.e-6)
        obs['perception'][:] = 3.
        raw = PerceptionActorCritic._actor_features(policy, obs)
        torch.testing.assert_close(policy.act_inference(obs), policy.actor.base(raw), rtol=0, atol=0)

    def test_gradients_and_privileged_isolation(self):
        alg, obs = algorithm()
        policy = alg.policy
        actor_obs = {k: obs[k] for k in policy.obs_groups['policy']}
        policy.act_inference(actor_obs).sum().backward()
        self.assertTrue(all(p.grad is None for p in policy.ball_head.parameters()))
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum() > 0 for p in policy.perception_encoder.parameters()))
        self.assertGreater(policy.actor.residual[-1].bias.grad.abs().sum(), 0.)
        policy.zero_grad(set_to_none=True)
        policy.ball_nll(obs).backward()
        self.assertTrue(all(p.grad is None for p in policy.actor.parameters()))
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum() > 0 for p in policy.ball_head.parameters()))
        expected = policy.act_inference(actor_obs)
        bad = obs.clone()
        for key in ('privileged', 'robot_vel', 'ball_status'):
            bad[key][:] = float('nan')
        torch.testing.assert_close(expected, policy.act_inference(bad), rtol=0, atol=0)

    def test_real_update_and_single_auxiliary_stage(self):
        alg, obs = algorithm()
        collect(alg, obs)
        head = [p.clone() for p in alg.policy.ball_head.parameters()]
        result = alg.update()
        self.assertTrue(all(torch.isfinite(torch.tensor(x)) for x in result.values()))
        self.assertEqual(result['aux/attempted_batches'], 2)
        self.assertGreater(result['aux/encoder_updates'], 0)
        self.assertEqual(alg.state_feedback_updates, result['aux/encoder_updates'])
        self.assertLessEqual(result['aux/stage_monitor_kl'], .01)
        self.assertEqual(result['aux/head_only_batches'], 0)
        self.assertTrue(any(not torch.equal(a, b) for a, b in zip(head, alg.policy.ball_head.parameters())))

    def test_kl_rejection_restores_all_parameters_and_adam(self):
        alg, obs = algorithm()
        with torch.no_grad():
            alg.policy.actor.residual[-1].bias.fill_(.5)
        collect(alg, obs)
        alg._update_ball_head()
        before = copy.deepcopy(alg.policy.state_dict())
        moments = copy.deepcopy(alg.ball_aux_optimizer.state_dict())
        updates = alg.state_feedback_updates
        alg.ball_aux_max_kl = 0.
        alg.ball_aux_optimizer.param_groups[0]['lr'] = .1
        alg._update_ball_head()
        self.assertEqual(alg.aux_metrics['aux/skipped_batches'], 2)
        self.assertEqual(alg.aux_metrics['aux/encoder_updates'], 0)
        self.assertEqual(alg.aux_metrics['aux/stage_monitor_kl'], 0.)
        self.assertEqual(alg.state_feedback_updates, updates)
        for key, value in alg.policy.state_dict().items():
            torch.testing.assert_close(value, before[key], rtol=0, atol=0)
        restored = alg.ball_aux_optimizer.state_dict()
        for pid, state in moments['state'].items():
            for key, value in state.items():
                torch.testing.assert_close(restored['state'][pid][key], value, rtol=0, atol=0)
        self.assertEqual(restored['param_groups'][0]['lr'], .1)

    def test_nonfinite_nll_fails_before_mutation(self):
        alg, obs = algorithm()
        collect(alg, obs)
        before = copy.deepcopy(alg.policy.state_dict())
        alg.storage.observations['privileged'][:] = float('nan')
        with self.assertRaises(FloatingPointError):
            alg._update_ball_head()
        for key, value in alg.policy.state_dict().items():
            torch.testing.assert_close(value, before[key], rtol=0, atol=0)

    def test_nonzero_feedback_matches_distribution_jit_and_onnx(self):
        import onnxruntime as ort
        for stable in (False, True):
            alg, obs = algorithm(stable)
            with torch.no_grad():
                alg.policy.actor.residual[-1].bias.copy_(torch.linspace(-1., 1., 29))
            obs['perception'][0] = 3.
            expected = alg.policy.act_inference(obs)
            alg.policy.update_distribution(obs)
            torch.testing.assert_close(alg.policy.action_mean, expected)
            with tempfile.TemporaryDirectory() as folder:
                export_depth_policy(alg.policy, obs, folder)
                model = torch.jit.load(str(Path(folder) / 'policy.pt'))
                torch.testing.assert_close(model(obs['proprio_hist'], obs['perception']), expected)
                session = ort.InferenceSession(str(Path(folder) / 'policy.onnx'), providers=['CPUExecutionProvider'])
                actual = session.run(None, {'flat': obs['proprio_hist'].numpy(), 'depth': obs['perception'].numpy()})[0]
                torch.testing.assert_close(torch.from_numpy(actual), expected, rtol=1.e-5, atol=1.e-6)

    @staticmethod
    def runner(alg):
        runner = BallRegressionOnPolicyRunner.__new__(BallRegressionOnPolicyRunner)
        runner.alg = alg
        runner.env = SimpleNamespace(unwrapped=SimpleNamespace())
        runner.device = 'cpu'
        runner.current_learning_iteration = 3
        runner.logger_type = 'tensorboard'
        return runner

    def test_checkpoint_counter_optimizer_and_bad_preflight(self):
        alg, obs = algorithm()
        collect(alg, obs);alg.update()
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'state.pt')
            self.runner(alg).save(path)
            state = torch.load(path, weights_only=False)
            new, _ = algorithm()
            runner = self.runner(new)
            runner.load(path)
            self.assertEqual(new.state_feedback_updates, alg.state_feedback_updates)
            torch.testing.assert_close(new.policy.act_inference(obs), alg.policy.act_inference(obs), rtol=0, atol=0)
            for mode in ('config', 'counter', 'optimizer', 'missing'):
                bad = copy.deepcopy(state)
                if mode == 'config':bad['state_feedback']['config']['history_decay'] = .7
                elif mode == 'counter':bad['state_feedback']['aux_updates'] = -1
                elif mode == 'optimizer':bad['ball_aux_optimizer_state_dict'] = None
                else:del bad['state_feedback']
                torch.save(bad, path)
                with patch.object(new.policy, 'load_state_dict') as loader:
                    with self.assertRaisesRegex(ValueError, 'state feedback'):
                        runner.load(path)
                    loader.assert_not_called()
            state['ball_aux_optimizer_state_dict'] = None
            torch.save(state, path)
            runner.load(path, load_optimizer=False)


    def test_stable_auxiliary_does_not_change_encoder_and_has_smooth_variance(self):
        alg, obs = algorithm(True)
        fixed_head(alg.policy, [0.] * 6 + [-6.] * 6)
        alg.policy.zero_grad(set_to_none=True)
        alg._auxiliary_loss(obs).backward()
        self.assertTrue(all(p.grad is None for p in alg.policy.perception_encoder.parameters()))
        self.assertTrue(all(p.grad is None for p in alg.policy.actor.parameters()))
        self.assertTrue((alg.policy.ball_head[-1].bias.grad[6:].abs() > 0).all())
        _, logstd = alg.policy.ball_distribution(obs)
        self.assertTrue(((logstd > -2.) & (logstd < 1.)).all())
        collect(alg, obs)
        before = copy.deepcopy(alg.policy.perception_encoder.state_dict())
        alg._update_ball_head()
        self.assertGreater(alg.aux_metrics['aux/predictor_updates'], 0)
        self.assertEqual(alg.aux_metrics['aux/encoder_updates'], 0)
        for key, value in alg.policy.perception_encoder.state_dict().items():
            torch.testing.assert_close(value, before[key], rtol=0, atol=0)
        alg.policy.zero_grad(set_to_none=True)
        alg.policy.act_inference(obs).sum().backward()
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum() > 0 for p in alg.policy.perception_encoder.parameters()))
        with torch.no_grad():alg.policy.actor.residual[-1].bias.fill_(100.)
        features = alg.policy._actor_features(obs)
        delta = alg.policy.actor(features) - alg.policy.actor.base(features[:, :992])
        self.assertLessEqual(delta.abs().max(), .1 + 1.e-6)

    def test_stable_checkpoint_rejects_legacy_algorithm_config(self):
        alg, obs = algorithm(True)
        collect(alg, obs);alg.update()
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'stable.pt')
            self.runner(alg).save(path)
            restored, _ = algorithm(True)
            self.runner(restored).load(path)
            self.assertEqual(restored.state_feedback_updates, alg.state_feedback_updates)
            self.assertEqual(restored.state_feedback_config['schema'], 2)
            torch.testing.assert_close(restored.policy.act_inference(obs), alg.policy.act_inference(obs))
            legacy, _ = algorithm()
            with patch.object(legacy.policy, 'load_state_dict') as loader:
                with self.assertRaisesRegex(ValueError, 'state feedback'):
                    self.runner(legacy).load(path)
                loader.assert_not_called()

    def test_explicit_v2_warm_start_is_exact_and_fresh(self):
        alg, obs = algorithm(True)
        with contextlib.redirect_stdout(io.StringIO()):
            v2 = PerceptionActorCritic(obs, alg.policy.obs_groups, 29, actor_hidden_dims=(32,),
                                      critic_hidden_dims=(32,), critic_obs_normalization=False)
        state = {'soccer_schema_version': 3, 'iter': 49999, 'model_state_dict': v2.state_dict(),
                 'agile_v2_recovery_curriculum': {'schema': 5, 'config': {'revision': 'v1_speed_only_20260925'}},
                 'amp_state_dict': None}
        runner = self.runner(alg);runner.current_learning_iteration = 0
        head = copy.deepcopy(alg.policy.ball_head.state_dict())
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'source.pt')
            bad = copy.deepcopy(state);bad['model_state_dict']['std'][0] = float('nan')
            torch.save(bad, path)
            with patch.object(alg.policy, 'load_state_dict') as loader:
                with self.assertRaisesRegex(ValueError, 'warm-start'):
                    runner.warm_start_from_v2(path)
                loader.assert_not_called()
            torch.save(state, path)
            runner.warm_start_from_v2(path)
            torch.testing.assert_close(alg.policy.act_inference(obs), v2.act_inference(obs), rtol=0, atol=0)
            torch.testing.assert_close(alg.policy.evaluate(obs), v2.evaluate(obs), rtol=0, atol=0)
            for key, value in alg.policy.ball_head.state_dict().items():
                torch.testing.assert_close(value, head[key], rtol=0, atol=0)
            self.assertEqual(len(alg.optimizer.state), 0)
            self.assertEqual(len(alg.ball_aux_optimizer.state), 0)
            self.assertEqual(alg.state_feedback_updates, 0)
            self.assertEqual(runner.current_learning_iteration, 0)
            runner.save(str(Path(folder) / 'new.pt'))
            self.assertEqual(torch.load(Path(folder) / 'new.pt', weights_only=False)['initialization']['kind'], 'v2_weights_only')


if __name__ == '__main__':
    unittest.main()
