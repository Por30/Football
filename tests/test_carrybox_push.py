"""Wall5 additive world-COM pushes preserve motion, curriculum and subset isolation."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
import torch
import test_carrybox as fixtures
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as wall5
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as wall4

RANGES = dict(x=(-.5,.5),y=(-.5,.5),z=(-.2,.2),roll=(-.52,.52),pitch=(-.52,.52),yaw=(-.78,.78))

class PushTests(unittest.TestCase):
    def environment(self, iteration, anchor=100):
        current=torch.tensor([[.85,.1,.2,.3,.4,.5],[-.5,.2,.1,-.4,.2,-.7],[1.,2.,3.,4.,5.,6.]])
        robot=NS(data=NS(root_vel_w=current.clone()),writes=[])
        def write(velocity,env_ids):
            robot.writes.append((env_ids.clone(),velocity.clone()));robot.data.root_vel_w[env_ids]=velocity
        robot.write_root_velocity_to_sim=write
        return NS(device='cpu',scene={'robot':robot},cfg=NS(push_warmup_iterations=1000,push_ramp_iterations=4000),
                  _walled=NS(curriculum=NS(anchor=anchor,iteration=iteration))),current

    def test_increment_sign_scale_and_untouched_survivors(self):
        ids=torch.tensor([0,2]);draw=torch.tensor([[1.,0.,.5,1.,0.,1.],[0.,1.,0.,.5,1.,0.]])
        delta=torch.tensor([[.5,-.5,0.,.52,-.52,.78],[-.5,.5,-.2,0.,.52,-.78]])
        for iteration,scale in ((3100,.5),(5100,1.),(9100,1.)):
            env,current=self.environment(iteration)
            with patch.object(torch,'rand',return_value=draw):wall5.push_velocity_increment(env,ids,RANGES)
            torch.testing.assert_close(env.scene['robot'].data.root_vel_w[ids],current[ids]+scale*delta)
            torch.testing.assert_close(env.scene['robot'].data.root_vel_w[1],current[1])
            self.assertEqual(len(env.scene['robot'].writes),1)

    def test_warmup_and_unanchored_never_write_or_erase_velocity(self):
        for iteration,anchor in ((0,None),(100,None),(99,100),(1100,100)):
            env,current=self.environment(iteration,anchor)
            wall5.push_velocity_increment(env,torch.tensor([0,1]),RANGES)
            self.assertEqual(env.scene['robot'].writes,[])
            torch.testing.assert_close(env.scene['robot'].data.root_vel_w,current)

    def test_original_wall4_semantics_and_draw_consumption_unchanged(self):
        ids=torch.tensor([0,2]);env,current=self.environment(5100)
        torch.manual_seed(18);wall4.push_velocity(env,ids,RANGES);sample=env.scene['robot'].data.root_vel_w[ids].clone();after=torch.get_rng_state()
        new,_=self.environment(5100);torch.manual_seed(18);wall5.push_velocity_increment(new,ids,RANGES)
        torch.testing.assert_close(new.scene['robot'].data.root_vel_w[ids],current[ids]+sample)
        self.assertTrue(torch.equal(torch.get_rng_state(),after))

if __name__=='__main__':unittest.main()
