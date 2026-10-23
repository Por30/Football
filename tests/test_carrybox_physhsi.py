"""PhysHSI migration: sampling, physics-step delay and termination boundaries."""
import ast
import types
import unittest
from pathlib import Path
import torch
import test_carrybox
from perceptual_ball.carrybox_physhsi import sample_hybrid, PhysicalActionDelay, interpolate

class ResetTests(unittest.TestCase):
    def test_hybrid_distribution_and_resampling(self):
        torch.manual_seed(42)
        skill, default = sample_hybrid(100000)
        label = torch.where(default, 0, skill+1)
        torch.testing.assert_close(torch.bincount(label,minlength=4)/len(label),
                                   torch.tensor([.2,8/15,2/15,2/15]),atol=.005,rtol=0)
        again, flag = sample_hybrid(100000)
        self.assertGreater(float(((again!=skill)|(default!=flag)).float().mean()),.4)
        self.assertTrue((skill[default]==0).all())

    def test_delay_extremes_physical_steps(self):
        q=torch.tensor([[.3,-.2],[.8,.5]])
        d=PhysicalActionDelay(q)
        d.reset(torch.arange(2),q,torch.tensor([4,0]))
        for tick in range(1,7):
            target=q+tick
            out=d.advance(target)
            torch.testing.assert_close(out[0],target[0])
            torch.testing.assert_close(out[1],q[1]+max(0,tick-4))
        self.assertEqual(d.steps,6)

    def test_partial_reset_does_not_clear_survivor(self):
        d=PhysicalActionDelay(torch.zeros(4,2));d.buffer.copy_(torch.arange(40).reshape(5,4,2))
        old=d.buffer.clone();ids=torch.tensor([3,1]);q=torch.tensor([[.7,.8],[-.5,.6]])
        d.reset(ids,q,torch.tensor([0,4]))
        torch.testing.assert_close(d.buffer[:,[0,2]],old[:,[0,2]])
        torch.testing.assert_close(d.buffer[:,ids],q[None].expand(5,-1,-1))

    def test_continuous_interpolation_and_antipodal_quaternion(self):
        t=torch.tensor([0.,.25,.9,1.])
        torch.testing.assert_close(interpolate(torch.tensor([[1.,2.],[3.,6.]]),t),torch.stack((1+2*t,2+4*t),-1))
        q=interpolate(torch.tensor([[1.,0,0,0],[-1.,0,0,0]]),t,True)
        torch.testing.assert_close(q.norm(dim=-1),torch.ones(4))
        self.assertTrue(torch.isfinite(q).all())
        torch.testing.assert_close(q.abs()[:,0],torch.ones(4))

class TerminationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=Path('source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_physhsi.py').read_text()
        tree=ast.parse(source);ns={'torch':torch}
        for node in tree.body:
            if isinstance(node,ast.FunctionDef) and node.name in ('fallen_pelvis','fallen_head','fallen_hip','box_speed'):
                exec(compile(ast.Module(body=[node],type_ignores=[]),'termination','exec'),ns)
        cls.functions=ns

    def test_named_bodies_height_origin_and_box_speed(self):
        # Ground at 4m prevents accidentally testing world height.
        origin=torch.zeros(4,3);origin[:,2]=4
        root=origin.clone();root[:,2]+=torch.tensor([.199,.201,.8,.8])
        bodies=origin[:,None].expand(-1,4,-1).clone();bodies[:,:,2]+=1.
        bodies[:,0,2]=4+torch.tensor([.599,.601,1.,1.])
        bodies[:,1,2]=4+torch.tensor([.149,.151,1.,1.])
        bodies[:,3,2]=0. # head_link decoy must not replace mid360
        robot=types.SimpleNamespace(data=types.SimpleNamespace(root_link_pos_w=root,body_link_pos_w=bodies),
            find_bodies=lambda names,**kw:([0],['mid360']) if names=='mid360_link' else ([1,2],names))
        box=types.SimpleNamespace(data=types.SimpleNamespace(root_lin_vel_w=torch.tensor([[3.01,0,0],[2.99,0,0],[0,-3.01,0],[0,0,50.]])))
        class Scene(dict):pass
        scene=Scene(robot=robot,box=box);scene.env_origins=origin
        e=types.SimpleNamespace(scene=scene)
        for name in ('fallen_pelvis','fallen_head','fallen_hip'):
            self.assertEqual(self.functions[name](e).tolist(),[True,False,False,False])
        self.assertEqual(self.functions['box_speed'](e).tolist(),[True,False,True,False])

if __name__=='__main__':unittest.main()
