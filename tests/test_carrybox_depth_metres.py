"""Wall5 metre-depth capture, label timing, legacy isolation and export units."""
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
import torch
import test_carrybox_asymmetric as asymmetric
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as parent
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task
from perceptual_ball.carrybox_walled import corrupt_depth_m
from perceptual_ball.rsl_rl_extensions.export import DepthPolicyExport
from isaaclab.utils.math import matrix_from_quat, quat_mul, quat_conjugate


def fixture(depth=None, metres=True):
    if depth is None:
        depth = torch.full((2, 2, 4), 1.5)
    n = len(depth)
    q = torch.tensor([[1., 0., 0., 0.]]).repeat(n, 1)
    camera = NS(mesh_manifest=[{'root': 'ground'}, {'root': 'env/Box'}, {'root': 'env/Wall'}],
                data=NS(output={'distance_to_image_plane': depth[..., None].clone(),
                                'mesh_id': torch.ones((*depth.shape, 1), dtype=torch.long)},
                        pos_w=torch.zeros(n, 3), quat_w_ros=q))
    box = NS(data=NS(root_pos_w=torch.tensor([[0., 0., 1.5]]).repeat(n, 1), root_quat_w=q))
    cfg = NS(depth_in_metres=metres, depth_noise_std_m=0., depth_edge_threshold_m=.15,
             depth_edge_probability=0., depth_hole_probability=0., depth_stereo_near_m=0.,
             depth_stereo_far_m=0., depth_max_delay_steps=1, depth_delay_probability=0.,
             depth_freeze_probability=0., depth_freeze_max_steps=3, pose_visibility_supervision=True)
    return NS(scene={'depth_camera': camera, 'box': box}, cfg=cfg, device='cpu', num_envs=n,
              common_step_counter=0, _walled=NS(paired=None))


class MetreDepthTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)

    def test_known_metres_nonfinite_clipping_misses_and_legacy(self):
        raw = torch.tensor([[[1.5, 2.5, .05, .1, 3., 4., float('nan'), float('inf'), -float('inf')]]])
        e = fixture(raw)
        expected = torch.tensor([[[1.5, 2.5, .1, .1, 3., 3., 3., 3., 3.]]])
        depth, pose = parent.captured_pair(e)
        torch.testing.assert_close(depth, expected, atol=0, rtol=0)
        self.assertEqual(pose.shape, (1, 10)); self.assertEqual(pose[0, 9], 1.)
        torch.testing.assert_close(e.scene['depth_camera'].data.output['distance_to_image_plane'][..., 0], raw, equal_nan=True)
        legacy = fixture(raw, False); del legacy.cfg.depth_in_metres
        old, old_pose = parent.captured_pair(legacy)
        torch.testing.assert_close(old, expected / 3.)
        torch.testing.assert_close(old_pose, pose)
        self.assertEqual(depth[0, 0, 0], 1.5)
        self.assertEqual(old[0, 0, 0], .5)

    def test_visibility_unit_boundaries_occlusion_and_holes(self):
        values = torch.tensor([.1, .099, 2.99, 3., 1.5, 1.5, 1.5])[:, None, None]
        e = fixture(values)
        e.scene['depth_camera'].data.output['mesh_id'][4] = 2  # Wall is nearest, not Box.
        pose = parent.base.box_pose_target(e)
        pose[5, 2] = 3.; pose[6, 2] = -.1
        expected = [True, False, True, False, False, False, False]
        self.assertEqual(task.pose_visible(e, values, pose).tolist(), expected)
        e.cfg.depth_in_metres = False
        self.assertEqual(task.pose_visible(e, values / 3., pose).tolist(), expected)
        e = fixture(); e.cfg.depth_hole_probability = 1.
        depth, target = parent.captured_pair(e)
        self.assertTrue((depth == 3.).all()); self.assertFalse(target[:, 9].any())
        edge = fixture(torch.tensor([[[1., 1., 2., 2.]]]))
        edge.cfg.depth_edge_probability = 1.
        edge.scene['depth_camera'].data.output['mesh_id'][:] = 2
        edge.scene['depth_camera'].data.output['mesh_id'][:, :, 1:3] = 1
        _, target = parent.captured_pair(edge)
        self.assertFalse(target[:, 9].any())  # Only Box hits were erased by the edge dropout.

    def test_capture_once_delay_freeze_and_same_step_partial_reset(self):
        e = fixture()
        with patch.object(parent, 'corrupt_depth_m', wraps=corrupt_depth_m) as corrupt:
            first = tuple(v.clone() for v in parent.captured_pair(e))
            parent.depth_image(e); parent.box_pose_target(e)
            self.assertEqual(corrupt.call_count, 1)
            e.cfg.depth_delay_probability = 1.; e.cfg.depth_freeze_probability = 1.
            e.common_step_counter = 1
            e.scene['depth_camera'].data.output['distance_to_image_plane'].fill_(2.)
            e.scene['depth_camera'].data.output['mesh_id'].fill_(2)
            e.scene['box'].data.root_pos_w[:, 2] = 2.
            for a, b in zip(parent.captured_pair(e), first): torch.testing.assert_close(a, b)
            e.common_step_counter = 2
            e.scene['depth_camera'].data.output['distance_to_image_plane'].fill_(2.5)
            e.scene['box'].data.root_pos_w[:, 2] = 2.5
            for a, b in zip(parent.captured_pair(e), first): torch.testing.assert_close(a, b)
            e._walled.paired.reset(torch.tensor([0]))
            e.scene['depth_camera'].data.output['mesh_id'][0] = 1
            depth, target = parent.captured_pair(e)
            torch.testing.assert_close(depth[0], torch.full_like(depth[0], 2.5))
            self.assertEqual(target[0, 2], 2.5); self.assertEqual(target[0, 9], 1.)
            torch.testing.assert_close(depth[1], first[0][1]); torch.testing.assert_close(target[1], first[1][1])
            self.assertEqual(corrupt.call_count, 4)

    def test_noise_amplitudes_are_metres_and_do_not_corrupt_misses(self):
        clean = torch.full((1000, 10, 10), 1.5)
        g = corrupt_depth_m(clean, gaussian_std=.02, stereo_near=0., stereo_far=0., edge_probability=0., hole_probability=0.)
        s = corrupt_depth_m(clean, gaussian_std=0., stereo_near=.008, stereo_far=.03, edge_probability=0., hole_probability=0.)
        self.assertAlmostEqual(float((g-clean).std()), .02, delta=.0003)
        self.assertAlmostEqual(float((s-clean).std()), .019, delta=.0003)
        miss = corrupt_depth_m(clean*2, gaussian_std=.02, stereo_near=.008, stereo_far=.03)
        self.assertTrue((miss == 3.).all())

    def test_critic123_rotation_columns_reconstruct_correct_relative_rotation(self):
        e = asymmetric.environment(); obs = task.critic_state(e)
        self.assertEqual(obs.shape, (4, 123))
        c0, c1 = obs[:, 99:102], obs[:, 102:105]
        actual = torch.stack((c0, c1, torch.linalg.cross(c0, c1)), -1)
        r, b = e.scene['robot'].data, e.scene['box'].data
        expected = matrix_from_quat(quat_mul(quat_conjugate(r.root_link_quat_w), b.root_quat_w))
        torch.testing.assert_close(actual, expected)

    def test_metres_export_and_json_contract_without_privileged_inputs(self):
        import json
        obs = asymmetric.observations(); obs['perception'] = .1 + obs['perception'] * 2.9
        policy = asymmetric.policy(obs); wrapper = torch.jit.script(DepthPolicyExport(policy, obs))
        torch.testing.assert_close(wrapper(obs['proprio'], obs['perception']), policy.act_inference(obs))
        self.assertFalse(any(k.startswith(('critic.', 'pose_head.')) for k in wrapper.state_dict()))
        e = task.Wall5CarryBoxEnv.__new__(task.Wall5CarryBoxEnv); e.cfg = fixture().cfg
        contract = json.loads(json.dumps(e.depth_contract))
        self.assertEqual(contract['output'], 'optical_z_metres'); self.assertEqual(contract['normalization'], 'none')
        self.assertEqual(contract['clip_range_m'], [.1, 3.]); self.assertEqual(contract['missing_value'], 3.)
        self.assertEqual(contract['shape'], [4, 27, 48])


if __name__ == '__main__': unittest.main()
