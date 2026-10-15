"""Regression checks for G1 frame/limit corrections and shared wall recipe."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import torch
import test_carrybox_x2 as old
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as wall
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_x2_rewards import reward_terms
from perceptual_ball.carrybox_walled import YawCurriculum
from isaaclab.utils.math import quat_from_euler_xyz,quat_apply

class WallParityTests(unittest.TestCase):
 def test_completed_metrics_ignore_randomized_timeout_age(self):
  s=NS(skills=torch.tensor([0,2]),achieved=torch.tensor([True,False]),actual_episode_steps=torch.tensor([10,3]))
  for name in ('episode_counts','success_counts','episode_steps','valid_amp_steps','tipped_counts','fell_counts'):
   setattr(s,name,torch.zeros(3,dtype=torch.long))
  e=NS(_walled=s,_carrybox_in_step=True,episode_length_buf=torch.tensor([900,900]),
       termination_manager=NS(get_term=lambda name:torch.tensor([True,False])))
  wall.record_episode_metrics(e,torch.tensor([0]))
  self.assertEqual(s.episode_steps.tolist(),[10,0,0]);self.assertEqual(s.valid_amp_steps.tolist(),[2,0,0])
  self.assertEqual(s.actual_episode_steps.tolist(),[0,3]);self.assertEqual(s.success_counts.tolist(),[1,0,0])
  wall.record_episode_metrics(e,torch.tensor([1]));self.assertEqual(s.valid_amp_steps.tolist(),[2,0,0])
  self.assertEqual(s.episode_counts.tolist(),[1,0,1]);self.assertEqual(s.episode_steps.tolist(),[10,0,3])
  e._carrybox_in_step=False;s.actual_episode_steps[0]=4
  wall.record_episode_metrics(e,torch.tensor([0]));self.assertEqual(s.episode_counts.tolist(),[1,0,1]);self.assertEqual(int(s.actual_episode_steps[0]),0)
 def test_head_com_rotation_translation_and_crouch(self):
  e=old.fixture();r=e.scene['robot'].data;r.body_com_pos_w=r.body_pos_w.clone()
  r.body_pos_w[:,0,2]=.35;r.root_pos_w[:,2]=.35
  q=quat_from_euler_xyz(torch.tensor([0.,.3,1.57,3.14]),torch.zeros(4),torch.zeros(4))
  r.body_com_pos_w[:,0]=r.body_pos_w[:,0]+quat_apply(q,torch.tensor([[0.,0.,.45]]).repeat(4,1))
  torch.testing.assert_close(wall.head_height(e),r.body_com_pos_w[:,0,2])
  self.assertEqual(wall.fallen(e).tolist(),[False,False,True,True])
  e.scene.env_origins[:,2]=5.;r.body_com_pos_w[:,:,2]+=5.;r.body_pos_w[:,:,2]+=5.;r.root_pos_w[:,2]+=5.
  self.assertEqual(wall.fallen(e).tolist(),[False,False,True,True])
  r.root_pos_w[0,2]=5.19;self.assertTrue(wall.fallen(e)[0])
 def test_standup_uses_physical_head_not_link_origin(self):
  e=old.fixture();r=e.scene['robot'].data;r.body_com_pos_w=r.body_pos_w.clone()
  r.body_pos_w[:,0,2]=.78;r.body_com_pos_w[:,0,2]=1.2
  self.assertTrue((reward_terms(e)['standup_task']>0).all())
  r.body_com_pos_w[:,0,2]=.79;e.common_step_counter+=1
  self.assertEqual(float(reward_terms(e)['standup_task'].sum()),0.)
 def test_only_knee_lower_reward_bound_changes(self):
  e=old.fixture();r=e.scene['robot'].data;e._walled.knees=[0,1]
  r.joint_pos=torch.tensor([[-.087,-.087,0.]]).repeat(4,1)
  r.joint_pos_limits=torch.tensor([[[-.087267,2.8798],[-.087267,2.8798],[-1.,1.]]]).repeat(4,1,1)
  r.soft_joint_pos_limits=torch.tensor([[[.061086,2.731446],[.061086,2.731446],[-.9,.9]]]).repeat(4,1,1)
  self.assertEqual(float(wall.reference_joint_pos_limits(e).sum()),0.)
  r.joint_pos[:,2]=1.;torch.testing.assert_close(wall.reference_joint_pos_limits(e),torch.full((4,),.1))
  r.joint_pos[:,0]=-.2;self.assertGreater(float(wall.reference_joint_pos_limits(e)[0]),.21)
  r.joint_pos[:,0]=2.8;self.assertGreater(float(wall.reference_joint_pos_limits(e)[0]),.16)
 def test_push_anchor_warmup_ramp_no_zero_velocity_write(self):
  e=old.fixture();e.cfg=NS(push_warmup_iterations=1000,push_ramp_iterations=4000);e._walled.curriculum=YawCurriculum('walled3')
  e.scene['robot'].data.root_vel_w=torch.full((4,6),.4);calls=[]
  e.scene['robot'].write_root_velocity_to_sim=lambda v,env_ids:calls.append(v.clone())
  ranges={k:(1.,1.) for k in ('x','y','z','roll','pitch','yaw')}
  wall.push_velocity(e,torch.arange(4),ranges);self.assertFalse(calls)
  for offset,expected in [(0,None),(999,None),(1000,None),(3000,.7),(5000,1.)]:
   e._walled.curriculum.set_iteration(65000+offset);before=len(calls);wall.push_velocity(e,torch.arange(4),ranges)
   if expected is None:self.assertEqual(len(calls),before)
   else:torch.testing.assert_close(calls[-1],torch.full((4,6),expected))
 def test_action_targets_use_parsed_joint_ids_and_keep_raw_action(self):
  # Exercise the exact small class without loading the simulator application.
  path=Path(__file__).parents[1]/'source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py'
  node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='WalledJointPositionAction')
  class Base:
   def process_actions(self,a):self._raw_actions=a.clone();self._processed_actions=a*.25+self._offset
  scope={'mdp':NS(JointPositionAction=Base)};exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),scope)
  action=scope['WalledJointPositionAction']();action._joint_ids=[2,0];action._offset=torch.tensor([[.1,-.1]])
  action._asset=NS(data=NS(joint_pos_limits=torch.tensor([[[-1.,1.],[-2.,2.],[-.5,.5]]])))
  raw=torch.tensor([[9.,-9.]]);action.process_actions(raw)
  torch.testing.assert_close(action._processed_actions,torch.tensor([[.5,-1.]]));torch.testing.assert_close(action._raw_actions,raw)
  self.assertTrue(action.target_saturation.all());action.process_actions(torch.zeros_like(raw))
  torch.testing.assert_close(action._processed_actions,action._offset);self.assertFalse(action.target_saturation.any())
