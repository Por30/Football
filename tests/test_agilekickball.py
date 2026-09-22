"""Boundary checks for the actual speed curriculum; no simulator import needed."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
import torch
import test_soccer_v3 as fixtures
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball import AgileKickballState, recovery_timed_out

SOURCE = Path(__file__).resolve().parents[1] / "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/curriculums.py"
spec = importlib.util.spec_from_file_location("agile_curriculums", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ramp = module.ramp_incoming_ball_speed


class SpeedCurriculumTests(unittest.TestCase):
    def env(self, step=0, n=4096):
        return SimpleNamespace(common_step_counter=step, num_envs=n,
                               _kickball=SimpleNamespace(serve_speed_range=(.4, .8)))

    def test_start_middle_end_and_clamping(self):
        env = self.env()
        for step, expected in [(0, .8), (120000, 1.4), (240000, 2.), (999999, 2.)]:
            env.common_step_counter = step
            self.assertAlmostEqual(ramp(env, [0]), expected)
            self.assertEqual(env._kickball.serve_speed_range[0], .4)

    def test_parallel_count_does_not_advance_curriculum(self):
        self.assertEqual(ramp(self.env(120000, 1), [0]), ramp(self.env(120000, 4096), [0]))

    def test_explicit_resume_progress_and_repeated_reset(self):
        env = self.env(240)
        for _ in range(5):
            self.assertAlmostEqual(ramp(env, [0], start_step=119760), 1.4)
        self.assertEqual(env.common_step_counter, 240)

    def test_invalid_parameters_leave_existing_range(self):
        for kwargs in ({"min_speed": 0}, {"initial_max_speed": 3.}, {"final_max_speed": float('nan')},
                       {"ramp_steps": 0}, {"ramp_steps": 1.5}, {"start_step": -1}):
            env = self.env()
            with self.assertRaises(ValueError):
                ramp(env, [0], **kwargs)
            self.assertEqual(env._kickball.serve_speed_range, (.4, .8))


class ContinuousRoundTests(unittest.TestCase):
    def setup_state(self):
        env, _ = fixtures.state_fixture()
        state = AgileKickballState(env)
        env._kickball = state
        state.reset(torch.arange(2))
        return env, state

    def ticks(self, env, state, count):
        for _ in range(count):
            env.common_step_counter += 1
            state.tick()

    def test_first_serve_and_second_round_keep_robot_state(self):
        env, state = self.setup_state()
        del env.reset_buf  # IsaacLab's initial reset occurs before this buffer exists.
        state.reset(torch.arange(2))
        env.reset_buf = torch.zeros(2, dtype=torch.bool)
        self.assertTrue(state.ball_active.all())
        baseline = state.serves.clone()
        robot_before = env.scene['robot'].data.root_pos_w.clone()
        def forbid_robot_write(*args, **kwargs):
            raise AssertionError('A ball round must not reset the robot')
        env.scene['robot'].write_root_pose_to_sim = forbid_robot_write
        env.scene['robot'].write_joint_state_to_sim = forbid_robot_write
        self.assertFalse(state.kick_success_flag.any())
        env.scene['ball'].data.root_pos_w[:, 0] = -.5
        env.scene['ball'].data.root_lin_vel_w[:, :2] = torch.tensor([.5, 0.])
        self.ticks(env, state, 1)
        self.assertTrue(state.just_missed.all())
        self.assertFalse(state.ball_active.any())
        self.ticks(env, state, 22)
        self.assertTrue((state.serves == baseline + 1).all())
        torch.testing.assert_close(robot_before, env.scene['robot'].data.root_pos_w)

    def test_stability_must_be_continuous_and_upright(self):
        env, state = self.setup_state()
        state.ball_active[:] = False
        state.steps_since_ball_ended[:] = 20
        state.wait_elapsed[:] = 1.
        self.ticks(env, state, 10)
        env.scene['robot'].data.projected_gravity_b[:, 2] = 1.  # inverted, despite zero XY tilt
        self.ticks(env, state, 1)
        self.assertTrue((state.stable_elapsed == 0).all())
        env.scene['robot'].data.projected_gravity_b[:, 2] = -1.
        self.ticks(env, state, 14)
        self.assertFalse(state.ball_active.any())
        self.ticks(env, state, 2)
        self.assertTrue(state.ball_active.all())

    def test_partial_reset_timeout_and_termination_priority(self):
        env, state = self.setup_state()
        self.ticks(env, state, 22)
        other_ball = env.scene['ball'].data.root_pos_w[1].clone()
        state.reset(torch.tensor([0]))
        self.assertTrue(state.ball_active[0])
        self.assertTrue(state.ball_active[1])
        torch.testing.assert_close(other_ball, env.scene['ball'].data.root_pos_w[1])
        state.ball_active[0] = False
        state.wait_elapsed[0] = 5.
        state.stable_elapsed[0] = 1.
        self.ticks(env, state, 1)
        self.assertTrue(recovery_timed_out(env)[0])
        self.assertFalse(state.ball_active[0])
        state.wait_elapsed[0] = 1.
        env.reset_buf[0] = True
        self.ticks(env, state, 1)
        self.assertFalse(state.ball_active[0])
        before = state.wait_elapsed.clone()
        state.tick()  # same control step is a no-op
        torch.testing.assert_close(before, state.wait_elapsed)


if __name__ == "__main__":
    unittest.main()
