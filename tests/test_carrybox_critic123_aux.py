"""Revision22: all captured frames supervise pose, privileged endpoints stay in critic."""
import unittest
import torch
import test_carrybox_asymmetric as asymmetric
from perceptual_ball.rsl_rl_extensions.carrybox import box_pose_loss
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5PPO


class AllFrameAuxTests(unittest.TestCase):
    def test_actual_ppo_objective_includes_hidden_far_and_behind_camera_targets(self):
        obs = asymmetric.observations()
        alg = CarryBoxWall5PPO(asymmetric.policy(obs), device='cpu', amp_coef=0., pose_aux_coef=1.0)
        target = obs['box_pose_target'].clone()
        target[:, :3] = torch.tensor([[.1, .2, 1.], [2., 1., 2.], [4., 2., 7.], [3., 1., -2.]])
        target[:, 9] = torch.tensor([1., 0., 0., 0.])
        target.requires_grad_(True)
        pred = torch.randn(4, 9, requires_grad=True)
        losses = alg._pose_loss(pred, target)
        expected = box_pose_loss(pred, target[:, :9].detach())
        for actual, value in zip(losses, expected):
            torch.testing.assert_close(actual, value)
        hidden = target.detach().clone(); hidden[:, 9] = 0.
        for actual, value in zip(alg._pose_loss(pred, hidden), losses):
            torch.testing.assert_close(actual, value)
        (alg.pose_aux_coef * sum(losses)).backward()
        self.assertTrue((pred.grad[:, :3].abs().sum(-1) > 0.).all())
        self.assertIsNone(target.grad)
        self.assertEqual(alg.amp_config['pose_target'], 'all_paired_xyz_rot6_visibility_diagnostic_only')

    def test_all_hidden_rollout_updates_pose_head_and_logs_full_supervision(self):
        obs = asymmetric.observations(); obs['box_pose_target'][:, 9] = 0.
        policy = asymmetric.policy(obs)
        alg = CarryBoxWall5PPO(policy, device='cpu', amp_coef=0., pose_aux_coef=1.,
                              num_learning_epochs=1, num_mini_batches=1)
        alg.init_storage('rl', 4, 2, obs, [29])
        before = [v.detach().clone() for v in policy.pose_head.parameters()]
        with torch.inference_mode():
            for _ in range(2):
                alg.act(obs)
                alg.process_env_step(obs, torch.ones(4), torch.zeros(4, dtype=torch.bool), {})
            alg.compute_returns(obs)
        result = alg.update()
        self.assertEqual(result['box_visible_fraction'], 0.)
        self.assertEqual(result['box_supervised_fraction'], 1.)
        self.assertGreater(result['box_position'], 0.)
        self.assertAlmostEqual(result['box_aux_weighted'], result['box_position'] + result['box_rotation'])
        self.assertTrue(any(not torch.equal(a, b) for a, b in zip(before, policy.pose_head.parameters())))


if __name__ == '__main__':
    unittest.main()
