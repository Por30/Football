"""G1 reward semantics, legacy defaults and reference-geometry boundaries."""
import json
import math
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import torch
import test_carrybox_distance3d as old
from isaaclab.utils.math import quat_from_euler_xyz
from perceptual_ball.carrybox_reward_geometry import (
    G1_ANCHORS, X2_ANCHORS, X2_REWARD_GEOMETRY, g1_reward_geometry, reward_geometry)
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as wall5
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as parent
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_x2_rewards import reward_terms


def fixture():
    e = old.fixture()
    e.cfg.reward_geometry = g1_reward_geometry()
    r = e.scene['robot'].data
    r.root_com_lin_vel_w = torch.zeros(4, 3)
    r.root_com_ang_vel_w = torch.zeros(4, 3)
    return e


class GeometryTests(unittest.TestCase):
    def test_corrected_head_anchor_and_unchanged_other_geometry(self):
        g = g1_reward_geometry()
        self.assertEqual(X2_ANCHORS['head'], 1.112)
        scale = G1_ANCHORS['head'] / 1.112
        for key, value in (('fallen_head', .4), ('success_head', .8), ('stand_head', .85)):
            self.assertAlmostEqual(g[key], value * scale, places=12)
        self.assertAlmostEqual(g['stand_head_exp'], 8. / scale, places=12)
        previous = json.loads((Path(__file__).resolve().parents[1] /
            'docs/carrybox/wall5_semantic_20261020/smoke.json').read_text())['contract']['reward_geometry']
        for key in previous.keys() - {'profile', 'fallen_head', 'success_head', 'stand_head', 'stand_head_exp'}:
            self.assertEqual(g[key], previous[key], key)

    def test_partial_standup_is_rewarded_after_head_correction(self):
        e = fixture(); r, b = e.scene['robot'].data, e.scene['box'].data
        g = e.cfg.reward_geometry
        r.root_pos_w[:, 2] = g['stand_pelvis']
        r.body_com_pos_w[:, 0, 2] = 1.0
        b.root_pos_w[:] = torch.tensor([.2, 0., g['carryup_box']])
        r.body_pos_w[:, 1:3] = b.root_pos_w[:, None]
        self.assertTrue((reward_terms(e)['standup_task'] > 0).all())
        e.cfg.reward_geometry = dict(g, success_head=.8 * G1_ANCHORS['head'] / .823)
        e.common_step_counter += 1
        self.assertEqual(reward_terms(e)['standup_task'].sum().item(), 0.)

    def test_split_height_termination_boundaries_and_union_counts(self):
        e = fixture(); r = e.scene['robot'].data; g = e.cfg.reward_geometry
        r.root_pos_w[:, 2] = g['fallen_pelvis'] + torch.tensor([-.001, 0., .1, -.001])
        r.body_com_pos_w[:, 0, 2] = g['fallen_head'] + torch.tensor([.1, 0., -.001, -.001])
        pelvis, head = parent.fallen_pelvis(e), parent.fallen_head(e)
        self.assertEqual(pelvis.tolist(), [True, False, False, True])
        self.assertEqual(head.tolist(), [False, False, True, True])
        torch.testing.assert_close(parent.fallen(e), pelvis | head)
        s = e._walled
        s.skills = torch.tensor([0, 0, 0, 0]); s.actual_episode_steps = torch.tensor([7, 8, 9, 10])
        for key in ('episode_counts', 'success_counts', 'episode_steps', 'valid_amp_steps', 'tipped_counts', 'fell_counts'):
            setattr(s, key, torch.zeros(3, dtype=torch.long))
        flags = {'fell_pelvis': pelvis, 'fell_head': head, 'tipped': torch.zeros(4, dtype=torch.bool)}
        e.termination_manager = NS(get_term=lambda key: flags[key])
        e.cfg.height_termination_terms = ('fell_pelvis', 'fell_head'); e._carrybox_in_step = True
        parent.record_episode_metrics(e, torch.arange(4))
        self.assertEqual(s.fell_counts.tolist(), [3, 0, 0])  # Both low still counts once.
        self.assertEqual(s.height_failure_counts['fell_pelvis'].tolist(), [2, 0, 0])
        self.assertEqual(s.height_failure_counts['fell_head'].tolist(), [2, 0, 0])
        self.assertEqual(s.episode_steps.tolist(), [34, 0, 0])
        self.assertEqual(s.actual_episode_steps.tolist(), [0, 0, 0, 0])
        # A head at 0.5 m was rejected at 0.593 m; corrected threshold allows it.
        r.root_pos_w[:, 2] = .4; r.body_com_pos_w[:, 0, 2] = .5
        self.assertFalse(parent.fallen(e).any())
        e.scene.env_origins[:, 2] += 3.; r.root_pos_w[:, 2] += 3.; r.body_com_pos_w[:, :, 2] += 3.
        self.assertFalse(parent.fallen(e).any())

    def test_measured_anchors_and_valid_crouch_clear_termination(self):
        result = json.loads((Path(__file__).resolve().parents[1] /
            'docs/carrybox/wall5_semantic_20261020/geometry.json').read_text())
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['anchors'], G1_ANCHORS)
        self.assertEqual(len(result['per_clip_upright']), 11)
        self.assertGreaterEqual(result['anchor_counts']['loco_upright'], 150)
        self.assertEqual(result['anchor_counts']['held_upright'], 32)
        g = g1_reward_geometry()
        for group in ('loco_direction', 'pickUp', 'carryWith'):
            self.assertGreater(result['groups'][group]['grounded_pelvis_m']['min'], g['fallen_pelvis'])
            self.assertGreater(result['groups'][group]['grounded_head_com_m']['min'], g['fallen_head'])
        self.assertLess(result['groups']['carryWith']['hand_to_reference_box_m']['max'], .15)

    def test_same_standing_horizontal_reach_and_scaled_height_curves(self):
        g, x = g1_reward_geometry(), X2_REWARD_GEOMETRY
        expected = math.sqrt(.7**2 - (.669-.125)**2)
        actual = math.sqrt(g['near_distance']**2 - (G1_ANCHORS['pelvis']-.125)**2)
        self.assertAlmostEqual(actual, expected, places=12)
        for prefix, scale, offset in (
                ('carryup', (G1_ANCHORS['box']-.125)/(.729-.125), .125),
                ('stand_pelvis', G1_ANCHORS['pelvis']/.669, 0.),
                ('stand_head', G1_ANCHORS['head']/1.112, 0.)):
            target_key = 'carryup_box' if prefix == 'carryup' else prefix
            exp_key = 'carryup_height_exp' if prefix == 'carryup' else prefix + '_exp'
            for deficit in (0., .05, .2):
                z = x[target_key] - deficit
                transformed = offset + (z-offset) * scale
                a = math.exp(-x[exp_key] * deficit)
                b = math.exp(-g[exp_key] * max(g[target_key]-transformed, 0.))
                self.assertAlmostEqual(a, b, places=12)
        self.assertEqual(reward_geometry(old.fixture()), x)

    def test_new_near_boundaries_shared_by_walk_pickup_search(self):
        e = fixture(); r, b = e.scene['robot'].data, e.scene['box'].data
        d = e.cfg.reward_geometry['near_distance']
        r.root_pos_w[:, 2] = .125
        b.root_pos_w[:] = torch.tensor([[d-.001, 0, .125], [d, 0, .125],
                                       [d+.001, 0, .125], [0, 0, .125]])
        r.body_pos_w[:, 1:3] = b.root_pos_w[:, None]
        r.joint_vel.fill_(2.); r.joint_acc.fill_(30.)
        t = reward_terms(e)
        self.assertEqual((t['carryup_task'] > 0).tolist(), [True, True, False, True])
        for key in ('slow_pickup', 'stable_grasp', 'arm_speed_pickup', 'arm_acc_pickup'):
            self.assertEqual((t[key] > 0).tolist(), [True, False, False, True])
        self.assertEqual((wall5.walk_task(e) == 1.5).tolist(), [True, False, False, True])
        self.assertTrue(all(torch.isfinite(v).all() for v in t.values()))
        b.root_pos_w[:, 1] = b.root_pos_w[:, 0]; b.root_pos_w[:, 0] = 0.
        self.assertEqual((parent.search_turn(e) > 0).tolist(), [False, False, True, False])

    def test_standup_and_search_use_pelvis_not_torso(self):
        e = fixture(); r, b = e.scene['robot'].data, e.scene['box'].data
        g = e.cfg.reward_geometry
        r.root_pos_w[:, 2] = g['stand_pelvis']
        r.body_pos_w[:, 0, 2] = g['stand_head']
        b.root_pos_w[:] = torch.tensor([.2, 0., g['carryup_box']])
        r.body_pos_w[:, 1:3] = b.root_pos_w[:, None]
        baseline = reward_terms(e)['standup_task'].clone()
        torch.testing.assert_close(baseline, torch.full((4,), 5.))
        z = torch.zeros(4)
        r.body_quat_w[:, e._walled.torso] = quat_from_euler_xyz(z+.6, z, z)
        r.body_ang_vel_w[:, e._walled.torso] = 10.
        r.body_lin_vel_w[:, e._walled.torso] = 5.
        e.common_step_counter += 1
        torch.testing.assert_close(reward_terms(e)['standup_task'], baseline)
        r.root_com_lin_vel_w[:, 0] = .7
        e.common_step_counter += 1
        self.assertTrue((reward_terms(e)['standup_task'] < baseline).all())
        b.root_pos_w[:, :2] = torch.tensor([0., 2.])
        r.root_com_ang_vel_w[:, 2] = 1.
        expected = .7 * math.exp(-.75*math.pi/2) + .3*math.tanh(1.)
        torch.testing.assert_close(parent.search_turn(e), torch.full((4,), expected))
        r.root_link_quat_w[:] = quat_from_euler_xyz(z+.3, z, z)
        e.common_step_counter += 1
        self.assertEqual(reward_terms(e)['standup_task'].sum().item(), 0.)

    def test_height_gates_contacts_and_world_translation(self):
        e = fixture(); r, b = e.scene['robot'].data, e.scene['box'].data
        g = e.cfg.reward_geometry
        r.root_pos_w[:, 2] = g['stand_pelvis']
        r.body_pos_w[:, 0, 2] = g['stand_head']
        b.root_pos_w[:] = torch.tensor([.2, 0., g['success_box']])
        b.root_pos_w[:, 2] += torch.tensor([-.001, 0., .001, .01])
        r.body_pos_w[:, 1:3] = b.root_pos_w[:, None]
        self.assertEqual((reward_terms(e)['standup_task'] > 0).tolist(), [False, False, True, True])
        # Only Box-filtered force matrices affect these rewards.
        before = reward_terms(e)['carryup_task'].clone()
        for side in ('left', 'right'):
            sensor = e.scene[side+'_box_contact'].data
            sensor.net_forces_w = torch.full((4, 1, 3), 1000.)
        e.common_step_counter += 1
        torch.testing.assert_close(reward_terms(e)['carryup_task'], before)
        for side in ('left', 'right'):
            e.scene[side+'_box_contact'].data.force_matrix_w[..., 2] = 8.
        e.common_step_counter += 1
        self.assertTrue((reward_terms(e)['carryup_task'] > before).all())
        r.joint_vel.fill_(2.)
        b.root_pos_w[:, 2] = g['held_box'] + torch.tensor([-.001, 0., .001, .01])
        r.body_pos_w[:, 1:3] = b.root_pos_w[:, None]
        self.assertEqual((parent.held_joint_excess(e) > 0).tolist(), [False, False, True, True])
        r.root_pos_w[:, 2] = g['fallen_pelvis'] + torch.tensor([-.001, 0., .1, .1])
        r.body_pos_w[:, 0, 2] = g['fallen_head'] + torch.tensor([.1, .1, -.001, 0.])
        self.assertEqual(parent.fallen(e).tolist(), [True, False, True, False])
        # Translation should not be assessed on an exact float32 equality plane.
        b.root_pos_w[:, 2] += .002
        r.body_pos_w[:, 1:3] = b.root_pos_w[:, None]
        e.common_step_counter += 1
        before = dict(reward_terms(e), walk5=wall5.walk_task(e),
                      search=parent.search_turn(e), held=parent.held_joint_excess(e))
        shift = torch.tensor([10., -8., 2.])
        e.scene.env_origins += shift; r.root_pos_w += shift
        r.body_pos_w += shift; b.root_pos_w += shift
        e.common_step_counter += 1
        after = dict(reward_terms(e), walk5=wall5.walk_task(e),
                     search=parent.search_turn(e), held=parent.held_joint_excess(e))
        for key in before:
            torch.testing.assert_close(after[key], before[key], atol=2e-5, rtol=2e-5)


if __name__ == '__main__':
    unittest.main()
