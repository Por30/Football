"""Wall5-only training boundary and auxiliary gradient contracts."""
import unittest
from types import SimpleNamespace as NS
import torch
import test_carrybox_wall5 as fixture
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import visible_box_pose_loss, Wall5AMP
from perceptual_ball.carrybox_wall5 import pack_task_frame
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_walled import failure_event
from perceptual_ball.carrybox_walled import PairedDepthBuffer
from isaaclab.utils.math import quat_from_euler_xyz, quat_apply, quat_mul


class TrainingTests(unittest.TestCase):
    def test_mask_blocks_unobservable_gradients_and_empty_loss(self):
        pred=torch.randn(4,9,requires_grad=True);target=torch.randn(4,10)
        target[:,9]=torch.tensor([1.,0.,1.,0.]);target[1,:9]=100000.;target[3,:9]=float('nan')
        loss=sum(visible_box_pose_loss(pred,target));loss.backward()
        self.assertTrue(torch.isfinite(loss));self.assertTrue((pred.grad[[1,3]]==0).all())
        target[:,9]=0;pred.grad=None
        loss=sum(visible_box_pose_loss(pred,target));loss.backward()
        self.assertEqual(loss.item(),0.);self.assertTrue((pred.grad==0).all())

    def test_visibility_range_occlusion_and_dropped_pixels(self):
        hits=torch.tensor([[[[1],[1]]],[[[2],[2]]],[[[1],[1]]],[[[1],[1]]],[[[1],[1]]]])
        camera=NS(mesh_manifest=[{'root':'ground'},{'root':'env/Box'},{'root':'env/Wall'}],data=NS(output={'mesh_id':hits}))
        env=NS(scene={'depth_camera':camera});depth=torch.full((5,1,2),.5);depth[2]=1
        pose=torch.zeros(5,9);pose[:,2]=torch.tensor([1.,1.,1.,3.1,-1.])
        self.assertEqual(task.pose_visible(env,depth,pose).tolist(),[True,False,False,False,False])
        paired=PairedDepthBuffer(depth,torch.cat((pose,task.pose_visible(env,depth,pose)[:,None]),-1),1)
        zero=torch.zeros(5,dtype=torch.long);one=torch.ones(5,dtype=torch.long)
        _,first=paired.update(0,depth,torch.cat((pose,torch.ones(5,1)),-1),zero,zero)
        old=first.clone()
        _,delayed=paired.update(1,depth+1,torch.zeros(5,10),one,one*2)
        torch.testing.assert_close(delayed,old)
        _,frozen=paired.update(2,depth+2,torch.zeros(5,10),zero,zero)
        torch.testing.assert_close(frozen,old)
        paired.reset(torch.tensor([0]))
        _,reset=paired.update(2,depth,torch.zeros(5,10),zero,zero)
        self.assertEqual(reset[0,9],0);torch.testing.assert_close(reset[1:],old[1:])

    def test_yaw_equivariance_and_box_cap(self):
        n=3;z=torch.zeros(n);q=quat_from_euler_xyz(z+.1,z+.2,z+.3)
        r=quat_from_euler_xyz(z,z,z+1.5)
        joints=torch.randn(n,29);ends=torch.randn(n,5,3);lin=torch.randn(n,3);ang=torch.randn(n,3)
        box=torch.tensor([[.1,.1,.2],[3.,3.,1.],[0.,0.,1.]])
        a=pack_task_frame(joints,q,ends,lin,ang,box)
        ends2=quat_apply(r[:,None].expand(-1,5,-1).reshape(-1,4),ends.reshape(-1,3)).reshape(n,5,3)
        b=pack_task_frame(joints,quat_mul(r,q),ends2,quat_apply(r,lin),ang,quat_apply(r,box))
        torch.testing.assert_close(a,b,atol=2e-6,rtol=1e-5)
        self.assertAlmostEqual(a[1,57:59].norm().item(),.7,places=6);self.assertEqual(a[1,59],0)

    def test_roll_boundary_and_failure_event_no_timeout_leak(self):
        roll=torch.tensor([.799,.801,-.799,-.801,0.]);z=torch.zeros(5)
        q=quat_from_euler_xyz(roll,z,z);env=NS(scene={'robot':NS(data=NS(root_quat_w=q))})
        self.assertEqual(task.tipped(env).tolist(),[False,True,False,True,False])
        env.termination_manager=NS(terminated=torch.tensor([False,True,False,True,True]),time_outs=torch.tensor([False,False,False,True,False]),get_term=lambda k:torch.tensor([True,True,True,True,False]))
        self.assertEqual(failure_event(env).tolist(),[0.,1.,0.,0.,0.])

    def test_adaptive_kl_and_constant_running_statistics(self):
        alg,obs=fixture.algorithm();alg.schedule='adaptive';alg.desired_kl=.01
        alg.policy.act(obs);mu=alg.policy.action_mean.detach();sigma=alg.policy.action_std.detach()
        initial=alg.learning_rate;alg._adapt_learning_rate(mu+10,sigma)
        self.assertLess(alg.learning_rate,initial)
        low=alg.learning_rate;alg._adapt_learning_rate(mu,sigma)
        self.assertGreater(alg.learning_rate,low)
        for group in alg.optimizer.param_groups:self.assertEqual(group['lr'],alg.learning_rate)
        d=Wall5AMP(600);d.set_statistics(torch.ones(3,600)*42)
        self.assertTrue((d.running_var==0).all());self.assertTrue(torch.isfinite(d(torch.ones(2,600)*1e6)).all())
        d.update_statistics(torch.ones(3,600)*44)
        torch.testing.assert_close(d.obs_mean,torch.full((600,),43.))
        torch.testing.assert_close(d.running_var,torch.ones(60))
        saved={k:v.clone() for k,v in d.state_dict().items()};d2=Wall5AMP(600);d2.load_state_dict(saved)
        for k,v in saved.items():torch.testing.assert_close(d2.state_dict()[k],v)

if __name__=='__main__':unittest.main()
