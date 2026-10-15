"""G1 termination must follow physical tilt, independent of yaw/quaternion sign."""
import unittest
from types import SimpleNamespace as NS
import torch
import test_carrybox_x2  # installs the existing lightweight IsaacLab test harness
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as wall
from isaaclab.utils.math import quat_from_euler_xyz,quat_mul,quat_conjugate,yaw_quat

class G1TerminationTests(unittest.TestCase):
 def test_roll_pitch_boundaries_with_heading(self):
  roll=torch.tensor([0.,.49,-.49,.51,-.51,0.,0.]);pitch=torch.tensor([0.,0.,0.,0.,0.,1.09,1.11]);yaw=torch.linspace(-3.,3.,7)
  q=quat_from_euler_xyz(roll,pitch,yaw);env=NS(scene={'robot':NS(data=NS(root_quat_w=q))})
  self.assertEqual(wall.tipped(env).tolist(),[False,False,False,True,True,False,True])
  env.scene['robot'].data.root_quat_w=-q;self.assertEqual(wall.tipped(env).tolist(),[False,False,False,True,True,False,True])
 def test_reference_clearance_partial_env_and_rotated_feet(self):
  points=torch.tensor([[-.1,0.,-.03],[.1,0.,-.03],[-.1,0.,.03],[.1,0.,.03]])
  q=quat_from_euler_xyz(torch.zeros(3),torch.tensor([0.,0.,.5]),torch.zeros(3))
  pos=torch.zeros(3,2,3);pos[:,:,2]=torch.tensor([.01,10.2,20.04])[:,None]
  robot=NS(body_link_pos_w=pos,body_link_quat_w=q[:,None].repeat(1,2,1))
  class Scene(dict):pass
  scene=Scene(robot=NS(data=robot));scene.env_origins=torch.tensor([[0.,0.,0.],[0.,0.,10.],[0.,0.,20.]])
  e=NS(scene=scene,_walled=NS(feet=[0,1],foot_support_points=[points,points]))
  value=wall.reference_ground_correction(e,torch.tensor([2,0,1]))
  self.assertAlmostEqual(float(value[1]),.025,places=6);self.assertEqual(float(value[2]),0.)
  self.assertGreater(float(value[0]),.03)
  # This helper only computes upward correction; callers preserve all other states.
  torch.testing.assert_close(pos[:,:,2],torch.tensor([.01,10.2,20.04])[:,None].expand(3,2))
 def test_source_physx_quaternion_roundtrip_and_heading_removal(self):
  q=quat_from_euler_xyz(torch.tensor([-.1,.2,0.]),torch.tensor([.1,-.2,0.]),torch.tensor([2.,-2.,0.]))
  xyzw=q[:,[1,2,3,0]];internal=xyzw[:,[3,0,1,2]];torch.testing.assert_close(q,internal)
  unyawed=quat_mul(quat_conjugate(yaw_quat(internal)),internal)
  self.assertTrue(torch.allclose(unyawed.norm(dim=-1),torch.ones(3)))
  e=NS(scene={'robot':NS(data=NS(root_quat_w=unyawed))});self.assertFalse(wall.tipped(e).any())

if __name__=='__main__':unittest.main()
