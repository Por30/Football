"""State-feedback v3 keeps v2 geometry/RNG and preserves legacy outcome tests."""
import tempfile
from pathlib import Path
from unittest.mock import patch
import unittest
import torch
import test_agilekickball_v2 as previous
import test_agilekickball_v3_outcome as legacy
import test_contact_outcome as outcome_learning
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v3 import AgileKickballV3State


class V3Tests(previous.V2Tests):
    def state(self, n=2):
        env, _ = previous.previous.fixtures.state_fixture(n)
        kb = AgileKickballV3State(env)
        env._kickball = kb
        kb.reset(torch.arange(n))
        kb._window_counts = kb._counts()
        return env, kb

    def test_physical_methods_identical_to_v2(self):
        for name in ('tick', 'reset', '_serve', '_sample_serve_speed', '_ready_to_serve',
                     'balanced', 'observation_status', '_sync_course'):
            self.assertIs(getattr(AgileKickballV3State, name), getattr(previous.AgileKickballV2State, name))
        _, new = self.state()
        _, old = previous.V2Tests().state()
        a, b = new.course_config.copy(), old.course_config.copy()
        a.pop('revision'); b.pop('revision')
        self.assertEqual(a.pop('initial_exposure_steps'), 0.)
        self.assertEqual(a, b)

    def test_explicit_initial_course_and_failed_revision_rejection(self):
        from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v3_feedback_legacy import AgileKickballV3State as FailedState
        env, _ = self.state()
        new = AgileKickballV3State(env, initial_exposure_steps=60000.)
        self.assertEqual(new.serve_distance_range, (1.3, 2.))
        self.assertEqual(new.serve_speed_range, (.4, 1.1))
        self.assertFalse(new.extension_unlocked)
        old = FailedState(env)
        with self.assertRaises(ValueError):new.load_curriculum_state_dict(old.curriculum_state_dict())
        with self.assertRaises(ValueError):old.load_curriculum_state_dict(new.curriculum_state_dict())

    def test_legacy_and_v2_checkpoints_rejected_before_weights(self):
        env, kb = self.state()
        for factory in (previous.V2Tests(), legacy.V3Tests()):
            oldenv, old = factory.state()
            with tempfile.TemporaryDirectory() as folder:
                path = str(Path(folder) / 'old.pt')
                self.runner(oldenv).save(path)
                runner = self.runner(env)
                with patch.object(runner.alg.policy, 'load_state_dict') as loader:
                    with self.assertRaisesRegex(ValueError, 'v3 curriculum'):
                        runner.load(path)
                    loader.assert_not_called()
            with self.assertRaises(ValueError):
                old.load_curriculum_state_dict(kb.curriculum_state_dict())


class V3RecoveryTests(previous.V2RecoveryTests):
    def setup_state(self):
        return V3Tests().state()


def load_tests(loader, tests, pattern):
    tests.addTests(loader.loadTestsFromModule(previous))
    tests.addTests(loader.loadTestsFromModule(legacy))
    tests.addTests(loader.loadTestsFromModule(outcome_learning))
    return tests


if __name__ == '__main__':
    unittest.main()
