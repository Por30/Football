"""Temporal labels, information boundaries, actual gradients and v3 recovery."""
import contextlib
import copy
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import torch
import test_soccer_v3 as fixtures
from perceptual_ball.rsl_rl_extensions.contact_outcome import (
    ContactOutcomePPO, OutcomeActorCritic, build_outcome_targets)
from perceptual_ball.rsl_rl_extensions.export import DepthPolicyExport
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v3_outcome import (
    AgileKickballV3State, outcome_training_state)


def states(t=12, n=3):
    result = torch.zeros(t, n, 10, dtype=torch.float64)
    result[..., 0] = 1
    result[..., 2] = torch.arange(t)[:, None]
    result[..., 4] = 1
    result[..., 8] = .8
    result[..., 9] = 1
    return result


def algorithm(coef=.1, n=4, steps=12, **kwargs):
    obs = fixtures.observations(n)
    obs['outcome_state'] = states(1, n)[0]
    obs['ball_status'] = torch.ones(n, 3)
    with contextlib.redirect_stdout(io.StringIO()):
        policy = OutcomeActorCritic(obs, {'policy': ['proprio_hist', 'perception'],
            'critic': ['proprio', 'robot_vel', 'privileged']}, 29,
            actor_hidden_dims=(32,), critic_hidden_dims=(32,), critic_obs_normalization=False)
    alg = ContactOutcomePPO(policy, device='cpu', num_learning_epochs=1,
        num_mini_batches=1, ball_aux_coef=.5, ball_aux_backtracking=True,
        ball_aux_epochs=1, outcome_aux_coef=coef, outcome_batch_size=8, **kwargs)
    alg.init_storage('rl', n, steps, obs, [29])
    return alg, obs


def collect(alg, obs):
    obs = obs.clone()
    with torch.inference_mode():
        for t in range(alg.storage.num_transitions_per_env):
            alg.act(obs)
            obs = obs.clone()
            obs['outcome_state'][:, 2] += .05
            if t == 7:
                obs['outcome_state'][0, 1] += 1
            alg.process_env_step(obs, torch.ones(len(obs)) * .01, torch.zeros(len(obs)), {})
        alg.compute_returns(obs)
    return obs


class TargetTests(unittest.TestCase):
    def test_source_frame_future_endpoint_and_event_window(self):
        s = states()
        s[0, 0, 4:6] = torch.tensor([0., 1.])  # source yaw +90 degrees
        s[8:, 0, 1] = 1  # event on last action of the horizon
        s[9:, 1, 1] = 1  # event is outside source t=0's horizon
        s[8, 0, 3] = 2.
        s[8, 0, 6:9] = torch.tensor([.1, .2, .7])
        y, mask = build_outcome_targets(s, torch.zeros(12, 3, 1), 8)
        self.assertEqual(y.shape, (4, 3, 6))
        torch.testing.assert_close(y[0, 0], torch.tensor([2., -8., .1, .2, .7, 1.]))
        self.assertEqual(y[0, 1, 5], 0)
        self.assertEqual(y[1, 1, 5], 1)
        self.assertTrue(mask.all())

    def test_last_transition_done_and_reserved_ball_are_masked(self):
        s = states()
        done = torch.zeros(12, 3, 1)
        done[7, 0] = 1
        s[8:, 1, 0] += 1
        # done[8] occurs AFTER obs[8], so the t=0, H=8 target is still valid.
        done[8, 2] = 1
        _, mask = build_outcome_targets(s, done, 8)
        self.assertEqual(mask[0].tolist(), [False, False, True])
        self.assertEqual(mask[1].tolist(), [False, False, False])

    def test_nan_interior_inactive_source_short_tail_and_input_errors(self):
        s = states()
        s[4, 0, 2] = float('nan')
        s[0, 1, 9] = 0
        _, mask = build_outcome_targets(s, torch.zeros(12, 3), 8)
        self.assertEqual(mask[0].tolist(), [False, False, True])
        for t in (2, 8):
            y, valid = build_outcome_targets(states(t), torch.zeros(t, 3), 8)
            self.assertEqual(y.shape, (0, 3, 6))
            self.assertEqual(valid.numel(), 0)
        with self.assertRaises(ValueError):
            build_outcome_targets(s, torch.zeros(11, 3), 8)

    def test_observation_read_is_side_effect_free_and_counter_precision(self):
        env, _ = fixtures.state_fixture()
        kb = AgileKickballV3State(env)
        env._kickball = kb
        kb.reset(torch.arange(2))
        kb.serves[0] = 2**24 + 1
        env.scene.env_origins[:, 2] = 2.
        kb.robot.data.root_pos_w[:, 2] = 2.8
        before = kb.curriculum_state_dict()
        target = outcome_training_state(env)
        self.assertEqual(target.dtype, torch.float64)
        self.assertEqual(target[0, 0].item(), 2**24 + 1)
        torch.testing.assert_close(target[:, 8], torch.full((2,), .8, dtype=torch.float64))
        self.assertEqual(before, kb.curriculum_state_dict())
        self.assertEqual(kb.last_tick, -1)


class LearningTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)

    def test_no_privileged_leak_in_prediction_inference_or_export(self):
        alg, obs = algorithm()
        actor_obs = {key: obs[key] for key in alg.policy.obs_groups['policy']}
        action = torch.zeros(4, 29, requires_grad=True)
        expected = alg.policy.act_inference(actor_obs)
        predicted = alg.policy.predict_outcome(actor_obs, action)
        corrupt = obs.clone()
        for key in ('privileged', 'outcome_state', 'robot_vel'):
            corrupt[key][:] = float('nan')
        torch.testing.assert_close(expected, alg.policy.act_inference(corrupt))
        torch.testing.assert_close(predicted, alg.policy.predict_outcome(corrupt, action))
        self.assertFalse(torch.equal(predicted, alg.policy.predict_outcome(actor_obs, action + 1)))
        predicted.sum().backward()
        self.assertIsNone(action.grad)
        wrapper = torch.jit.script(DepthPolicyExport(alg.policy, obs))
        torch.testing.assert_close(expected, wrapper(obs['proprio_hist'], obs['perception']))
        self.assertNotIn('outcome_head', str(wrapper.state_dict().keys()))

    def test_actual_ppo_and_auxiliary_updates_are_finite(self):
        alg, obs = algorithm()
        collect(alg, obs)
        before = [p.clone() for p in alg.policy.outcome_head.parameters()]
        result = alg.update()
        self.assertEqual(result['outcome/valid_count'], 16)
        self.assertEqual(result['outcome/sample_count'], 16)
        self.assertGreater(result['outcome/encoder_updates'], 0)
        self.assertLessEqual(result['outcome/stage_monitor_kl'], .005)
        self.assertTrue(all(torch.isfinite(torch.tensor(v)) for v in result.values()))
        self.assertTrue(any(not torch.equal(a, b) for a, b in zip(before, alg.policy.outcome_head.parameters())))

    def test_auxiliary_alone_learns_shared_encoder(self):
        alg, obs = algorithm()
        collect(alg, obs)
        before = [p.clone() for p in alg.policy.perception_encoder.parameters()]
        result = alg._update_outcome()
        self.assertGreater(result['outcome/encoder_updates'], 0)
        self.assertTrue(any(not torch.equal(a, b) for a, b in zip(before, alg.policy.perception_encoder.parameters())))

    def test_kl_rejection_restores_encoder_and_adam_momentum(self):
        alg, obs = algorithm()
        collect(alg, obs)
        alg._update_outcome()  # create nonzero Adam momentum
        encoder = list(alg.policy.perception_encoder.parameters())
        before = [p.clone() for p in encoder]
        momentum = [copy.deepcopy(alg.outcome_optimizer.state[p]) for p in encoder]
        head_before = [p.clone() for p in alg.policy.outcome_head.parameters()]
        alg.outcome_config['max_kl'] = 0.
        alg.outcome_optimizer.param_groups[0]['lr'] = .1
        result = alg._update_outcome()
        self.assertEqual(result['outcome/encoder_updates'], 0)
        self.assertEqual(result['outcome/head_only_batches'], 2)
        self.assertEqual(result['outcome/stage_monitor_kl'], 0.)
        for value, saved, state in zip(encoder, before, momentum):
            torch.testing.assert_close(value, saved, rtol=0, atol=0)
            for key, item in state.items():
                torch.testing.assert_close(alg.outcome_optimizer.state[value][key], item, rtol=0, atol=0)
        self.assertTrue(any(not torch.equal(a, b) for a, b in zip(head_before, alg.policy.outcome_head.parameters())))

    def test_empty_and_nonfinite_inputs_do_not_create_updates(self):
        alg, obs = algorithm()
        collect(alg, obs)
        alg.storage.observations['perception'][:] = float('nan')
        before = copy.deepcopy(alg.policy.state_dict())
        result = alg._update_outcome()
        self.assertEqual(result['outcome/skipped'], 1.)
        self.assertEqual(result['outcome/nonfinite_source_count'], 16)
        self.assertEqual(len(alg.outcome_optimizer.state), 0)
        for key, value in alg.policy.state_dict().items():
            torch.testing.assert_close(value, before[key])

    def test_ablation_skips_aux_and_short_rollout_fails_early(self):
        alg, obs = algorithm(coef=0.)
        collect(alg, obs)
        with patch.object(alg, '_update_outcome') as update:
            alg.update()
            update.assert_not_called()
        self.assertIsNone(alg.outcome_optimizer)
        with self.assertRaisesRegex(ValueError, 'longer'):
            algorithm(steps=8)

    @staticmethod
    def runner(alg):
        runner = BallRegressionOnPolicyRunner.__new__(BallRegressionOnPolicyRunner)
        runner.alg = alg
        runner.env = SimpleNamespace(unwrapped=SimpleNamespace())
        runner.device = 'cpu'
        runner.current_learning_iteration = 12
        runner.logger_type = 'tensorboard'
        return runner

    def test_checkpoint_optimizer_restore_and_preflight(self):
        alg, obs = algorithm()
        collect(alg, obs)
        alg.update()
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'outcome.pt')
            self.runner(alg).save(path)
            state = torch.load(path, weights_only=False)
            new, _ = algorithm()
            runner = self.runner(new)
            runner.load(path)
            for key, value in alg.policy.state_dict().items():
                torch.testing.assert_close(new.policy.state_dict()[key], value, rtol=0, atol=0)
            for old_p, new_p in zip(alg.policy.perception_encoder.parameters(), new.policy.perception_encoder.parameters()):
                for key, value in alg.outcome_optimizer.state[old_p].items():
                    torch.testing.assert_close(new.outcome_optimizer.state[new_p][key], value, rtol=0, atol=0)
            for kind in ('missing', 'config', 'optimizer'):
                broken = copy.deepcopy(state)
                if kind == 'missing':
                    del broken['contact_outcome']
                elif kind == 'config':
                    broken['contact_outcome']['config']['horizon'] = 7
                else:
                    broken['contact_outcome']['optimizer'] = None
                torch.save(broken, path)
                with patch.object(new.policy, 'load_state_dict') as loader:
                    with self.assertRaisesRegex(ValueError, 'contact outcome'):
                        runner.load(path)
                    loader.assert_not_called()
            # Inference needs the model/config, but not training optimizer moments.
            runner.load(path, load_optimizer=False)


if __name__ == '__main__':
    unittest.main()
