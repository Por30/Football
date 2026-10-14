"""Wider serve geometry plus inherited v2 speed/recovery/checkpoint regressions."""
import tempfile
from pathlib import Path
from unittest.mock import patch
import unittest
import torch
import test_agilekickball_v2 as previous
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v2 import AgileKickballV2State
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v3 import AgileKickballV3State
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.terminations import walked_away_from_anchor


class V3Tests(previous.V2Tests):
    def state(self, n=2):
        env, _ = previous.previous.fixtures.state_fixture(n)
        kb = AgileKickballV3State(env)
        env._kickball = kb
        kb.reset(torch.arange(n))
        kb._window_counts = kb._counts()
        return env, kb

    def test_bootstrap_exact_v1_ranges_serve_and_rng(self):
        # At initial exposure v3 is physically identical; speed stays identical
        # throughout bootstrap, while only the spatial distribution expands.
        env, kb = self.state(32)
        oldenv, old = previous.V2Tests().state(32)
        for exposure, distances, width in [(0., (.5, .7), .25),
                (30000., (.9, 1.85), .3), (60000., (1.3, 3.), .35),
                (240000., (1.3, 3.), .35)]:
            for state in (kb, old):
                state.exposure_offset = exposure
                state._sync_course()
            self.assertEqual(kb.serve_speed_range, old.serve_speed_range)
            for actual, expected in zip(kb.serve_distance_range, distances):
                self.assertAlmostEqual(actual, expected)
            self.assertEqual(kb.serve_aim_offset_range, (-width, width))
            if exposure == 0:
                torch.manual_seed(42); kb.reset(torch.arange(32)); rng = torch.get_rng_state()
                torch.manual_seed(42); old.reset(torch.arange(32))
                torch.testing.assert_close(torch.get_rng_state(), rng, rtol=0, atol=0)
                for key in ('root_pos_w', 'root_lin_vel_w'):
                    torch.testing.assert_close(getattr(env.scene['ball'].data, key),
                                               getattr(oldenv.scene['ball'].data, key), rtol=0, atol=0)

    def test_rotated_translated_serve_geometry_and_partial_reset(self):
        env, kb = self.state(4096)
        robot = env.scene['robot'].data
        robot.root_pos_w[:, :2] = torch.tensor([4., -3.])
        yaw = torch.tensor(1.1)
        robot.root_quat_w[:] = torch.tensor([(yaw / 2).cos(), 0., 0., (yaw / 2).sin()])
        kb.exposure_offset = 60000.; kb._sync_course()
        kb.serve_speed_override = (6., 6.)
        torch.manual_seed(42); kb.reset(torch.arange(4096))
        pos = kb.ball.data.root_pos_w[:, :2] - kb.anchor_xy
        vel = kb.ball.data.root_lin_vel_w[:, :2]
        distance = pos.norm(dim=-1)
        radial = pos / distance[:, None]
        travel_time = -distance / (vel * radial).sum(-1)
        aim = pos + vel * travel_time[:, None]
        perp = torch.stack([radial[:, 1], -radial[:, 0]], -1)
        offset = (aim * perp).sum(-1)
        self.assertTrue(((distance >= 1.3 - 1e-5) & (distance <= 3. + 1e-5)).all())
        self.assertGreater(distance.max().item(), 2.95)
        self.assertTrue((offset.abs() <= .35 + 1e-5).all())
        self.assertLess(offset.min().item(), -.33); self.assertGreater(offset.max().item(), .33)
        torch.testing.assert_close(vel.norm(dim=-1), torch.full_like(distance, 6.))
        self.assertTrue((travel_time > 0).all())
        self.assertLess(offset.mean().abs().item(), .03)
        pose_before = kb.ball.data.root_pos_w.clone()
        kb.reset(torch.tensor([0]))
        torch.testing.assert_close(kb.ball.data.root_pos_w[1:], pose_before[1:])

    def test_three_metre_serve_survives_and_four_metre_exit_ends(self):
        env, kb = self.state(64)
        kb.serve_distance_range = (3., 3.)
        kb.reset(torch.arange(64))
        self.tick(env, kb, 1)
        self.assertTrue(kb.ball_active.all())
        kb.ball.data.root_pos_w[:, :2] = kb.anchor_xy + torch.tensor([4.01, 0.])
        self.tick(env, kb, 1)
        self.assertFalse(kb.ball_active.any())

    def test_robot_travel_boundary(self):
        env, kb = self.state(4)
        env.scene['robot'].data.root_pos_w[:, 0] = torch.tensor([.59, .61, 1.19, 1.21])
        self.assertEqual(walked_away_from_anchor(env, 1.2).tolist(), [False, False, False, True])
        self.assertEqual(walked_away_from_anchor(env, .6).tolist(), [False, True, True, True])

    def test_v2_checkpoint_rejected_before_policy_load(self):
        oldenv, old = previous.V2Tests().state()
        env, kb = self.state()
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'v2.pt')
            self.runner(oldenv).save(path)
            runner = self.runner(env)
            with patch.object(runner.alg.policy, 'load_state_dict') as loader:
                with self.assertRaisesRegex(ValueError, 'v3 curriculum'):
                    runner.load(path)
                loader.assert_not_called()
            with self.assertRaises(ValueError):
                kb.load_curriculum_state_dict(old.curriculum_state_dict())


class V3RecoveryTests(previous.V2RecoveryTests):
    def setup_state(self):
        return V3Tests().state()


def load_tests(loader, tests, pattern):
    tests.addTests(loader.loadTestsFromModule(previous))
    return tests


if __name__ == '__main__':
    unittest.main()
