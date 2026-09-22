"""Reward-phase and event-pulse checks on production functions/state."""
import unittest
import torch
import test_agilekickball_v1 as v1
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.rewards import (
    stand_task, stand_for_kick_task, kick_bonus, miss_penalty,
)


class RewardTests(unittest.TestCase):
    def test_stand_scale_before_kick_after_kick_and_waiting(self):
        env,kb=v1.V1Tests().state(4)
        kb.ball_active[:]=torch.tensor([True,True,False,False])
        kb.ball_kicked[:]=torch.tensor([False,True,False,True])
        original=stand_task(env,target_height=.8)
        torch.testing.assert_close(stand_for_kick_task(env),original*torch.tensor([.25,1.,1.,1.]))
        self.assertTrue((original>0).all())

    def test_helper_is_read_only_and_preserves_base_stability_shape(self):
        env,kb=v1.V1Tests().state()
        q=env.scene['robot'].data
        q.root_lin_vel_w[0,0]=.3;q.projected_gravity_b[1,0]=.15
        before=[kb.ball_active.clone(),kb.ball_kicked.clone(),q.root_pos_w.clone(),q.root_lin_vel_w.clone()]
        baseline=stand_task(env,target_height=.8)
        for _ in range(3):torch.testing.assert_close(stand_for_kick_task(env),baseline*.25)
        for a,b in zip(before,[kb.ball_active,kb.ball_kicked,q.root_pos_w,q.root_lin_vel_w]):torch.testing.assert_close(a,b)
        self.assertEqual(kb.last_tick,-1)

    def test_kick_pulse_once_then_full_standing_for_recovery(self):
        env,kb=v1.V1Tests().state();ball=env.scene['ball'].data
        ball.root_pos_w[:]=torch.tensor([.2,0.,.11]);ball.root_lin_vel_w[:]=torch.tensor([.8,0.,0.])
        v1.V1Tests().tick(env,kb)
        torch.testing.assert_close(kick_bonus(env),torch.ones(2))
        torch.testing.assert_close(stand_for_kick_task(env),stand_task(env,target_height=.8))
        self.assertFalse(miss_penalty(env).any())
        v1.V1Tests().tick(env,kb)
        self.assertFalse(kick_bonus(env).any());self.assertTrue(kb.ball_kicked.all())

    def test_miss_pulse_once_and_recovery_not_penalized_for_standing(self):
        env,kb=v1.V1Tests().state();ball=env.scene['ball'].data
        ball.root_pos_w[:]=torch.tensor([-.5,0.,.11]);ball.root_lin_vel_w[:]=torch.tensor([.5,0.,0.])
        v1.V1Tests().tick(env,kb)
        self.assertFalse(kb.ball_active.any());self.assertFalse(kick_bonus(env).any())
        torch.testing.assert_close(miss_penalty(env),torch.ones(2))
        torch.testing.assert_close(stand_for_kick_task(env),stand_task(env,target_height=.8))
        v1.V1Tests().tick(env,kb);self.assertFalse(miss_penalty(env).any())


if __name__=='__main__':unittest.main()
