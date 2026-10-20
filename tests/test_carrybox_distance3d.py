"""Wall5 X2 task gates: XYZ proximity, XY movement, legacy task isolation."""
import math
import unittest
from types import SimpleNamespace as NS

import torch
import test_carrybox_x2 as legacy
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as parent
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as wall5
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_x2_rewards import reward_terms


def fixture():
    env = legacy.fixture()
    env.cfg = NS(task_box_distance_3d=True)
    r = env.scene['robot'].data
    r.root_link_pos_w = r.root_pos_w
    r.root_link_quat_w = r.root_quat_w
    r.root_link_lin_vel_w = torch.zeros(4, 3)
    r.projected_gravity_b = r.GRAVITY_VEC_W
    env._walled.search = torch.ones(4, dtype=torch.bool)
    return env


class DistanceTests(unittest.TestCase):
    def test_height_changes_gate_and_legacy_defaults_remain_xy(self):
        env = fixture()
        r, b = env.scene['robot'].data, env.scene['box'].data
        r.root_pos_w[:, 2] = torch.tensor([.78, .78, .55, .55])
        b.root_pos_w[:] = torch.tensor([[.33, 0., .125], [.20, 0., .125],
                                           [.60, 0., .125], [.50, 0., .125]])
        r.body_pos_w[:, 1:3] = b.root_pos_w[:, None]
        r.joint_vel.fill_(2.)
        r.joint_acc.fill_(30.)
        delta = b.root_pos_w - r.root_pos_w
        distance = parent.task_box_distance(env, delta)
        torch.testing.assert_close(distance, torch.sqrt(delta.square().sum(-1)))
        self.assertEqual((distance < .7).tolist(), [False, True, False, True])
        terms = reward_terms(env)
        self.assertEqual((terms['carryup_task'] > 0).tolist(), [False, True, False, True])
        self.assertEqual((terms['slow_pickup'] > 0).tolist(), [False, True, False, True])
        for key in ('stable_grasp', 'arm_speed_pickup', 'arm_acc_pickup'):
            self.assertEqual((terms[key] > 0).tolist(), [False, False, False, True], key)
        env.cfg.task_box_distance_3d = False
        env.common_step_counter += 1
        old = reward_terms(env)
        self.assertTrue((old['carryup_task'] > 0).all())
        self.assertTrue((old['slow_pickup'] > 0).all())
        for key in ('stable_grasp', 'arm_speed_pickup', 'arm_acc_pickup'):
            self.assertEqual((old[key] > 0).tolist(), [False, False, True, True])
        del env.cfg.task_box_distance_3d
        env.common_step_counter += 1
        for key, value in reward_terms(env).items():
            torch.testing.assert_close(value, old[key], rtol=0, atol=0)
        del env.cfg
        torch.testing.assert_close(parent.task_box_distance(env, delta), delta[:, :2].norm(dim=-1))

    def test_exact_threshold_retains_strict_and_inclusive_gates(self):
        env = fixture()
        r, b = env.scene['robot'].data, env.scene['box'].data
        r.root_pos_w[:, 2] = .125
        b.root_pos_w[:] = torch.tensor([[.6999, 0., .125], [.7, 0., .125],
                                        [.7001, 0., .125], [0., 0., .125]])
        r.body_pos_w[:, 1:3] = b.root_pos_w[:, None]
        r.joint_vel.fill_(2.)
        r.joint_acc.fill_(30.)
        terms = reward_terms(env)
        self.assertEqual((terms['carryup_task'] > 0).tolist(), [True, True, False, True])
        for key in ('slow_pickup', 'stable_grasp', 'arm_speed_pickup', 'arm_acc_pickup'):
            self.assertEqual((terms[key] > 0).tolist(), [True, False, False, True])
        self.assertEqual((terms['walk_task'] == 1.5).tolist(), [True, False, False, True])
        self.assertTrue(all(torch.isfinite(v).all() for v in terms.values()))

    def test_horizontal_velocity_is_not_divided_by_xyz_distance(self):
        env = fixture()
        r, b = env.scene['robot'].data, env.scene['box'].data
        r.root_pos_w[:, 2] = .78
        b.root_pos_w[:] = torch.tensor([[.33, 0., .125], [.33, 0., -.5],
                                        [0., 0., -.5], [.2, 0., .125]])
        r.root_link_lin_vel_w[:, 0] = .85
        r.body_lin_vel_w[:, env._walled.torso, 0] = .85
        for value in (wall5.walk_task(env), reward_terms(env)['walk_task']):
            torch.testing.assert_close(value[[0, 1, 3]], torch.full((3,), 1.5))
            self.assertTrue(torch.isfinite(value).all())
            self.assertLess(value[2], .53)  # Zero XY direction stays finite.
        r.root_link_lin_vel_w.zero_()
        value = wall5.walk_task(env)
        self.assertAlmostEqual(value[0].item(), math.exp(-5 * .85**2) + .5, places=6)
        self.assertEqual(value[3], 1.5)

    def test_stability_exemption_and_search_use_same_xyz_metric(self):
        env = fixture()
        r, b = env.scene['robot'].data, env.scene['box'].data
        r.root_pos_w[:, 2] = .55
        b.root_pos_w[:] = torch.tensor([[0., .6, .125], [0., .5, .125],
                                        [0., .6, .125], [0., .5, .125]])
        balance = wall5.locomotion_stability(env)
        torch.testing.assert_close(balance, torch.tensor([math.exp(-.2), 1., math.exp(-.2), 1.]))
        turn = parent.search_turn(env)
        expected = .7 * math.exp(-.75 * math.pi / 2)
        torch.testing.assert_close(turn, torch.tensor([expected, 0., expected, 0.]))
        env.cfg.task_box_distance_3d = False
        torch.testing.assert_close(wall5.locomotion_stability(env), torch.ones(4))
        torch.testing.assert_close(parent.search_turn(env), torch.zeros(4))

    def test_world_translation_preserves_reward_and_stability(self):
        env = fixture()
        r, b = env.scene['robot'].data, env.scene['box'].data
        r.root_pos_w[:, 2] = .55
        b.root_pos_w[:] = torch.tensor([[0., .6, .125], [0., .5, .125],
                                        [0., .6, .125], [0., .5, .125]])
        before = dict(reward_terms(env), balance=wall5.locomotion_stability(env),
                      walk5=wall5.walk_task(env), search=parent.search_turn(env))
        shift = torch.tensor([100., -25., 5.])
        env.scene.env_origins += shift
        r.root_pos_w += shift
        r.body_pos_w += shift
        b.root_pos_w += shift
        env.common_step_counter += 1
        after = dict(reward_terms(env), balance=wall5.locomotion_stability(env),
                     walk5=wall5.walk_task(env), search=parent.search_turn(env))
        for key in before:
            torch.testing.assert_close(after[key], before[key], atol=2e-5, rtol=2e-5)


if __name__ == '__main__':
    unittest.main()
