"""Numerical handoff boundaries using production rewards, noise and events."""
import math
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from pathlib import Path
import ast
import json
import re
import torch
import test_carrybox as baseline
from isaaclab.utils.math import quat_from_euler_xyz
from perceptual_ball.carrybox_walled import corrupt_depth_m, PairedDepthBuffer
from perceptual_ball.carrybox_amp import DEFAULT_DATASET_PATH
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as wall
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_x2_rewards import reward_terms


class Scene(dict):
    pass


def fixture():
    n=4
    q=torch.tensor([[1.,0.,0.,0.]]).repeat(n,1)
    robot=NS(root_pos_w=torch.tensor([[0.,0.,.66]]).repeat(n,1),root_quat_w=q,
        body_pos_w=torch.tensor([[[0.,0.,.85],[.6,0.,.64],[.6,0.,.64],[0.,0.,.7]]]).repeat(n,1,1),
        body_quat_w=q[:,None].repeat(1,4,1), body_lin_vel_w=torch.zeros(n,4,3),body_ang_vel_w=torch.zeros(n,4,3),
        GRAVITY_VEC_W=torch.tensor([[0.,0.,-1.]]).repeat(n,1),joint_vel=torch.zeros(n,2),joint_acc=torch.zeros(n,2))
    box=NS(root_pos_w=torch.tensor([[.6,0.,.64]]).repeat(n,1),root_lin_vel_w=torch.zeros(n,3),root_ang_vel_w=torch.zeros(n,3))
    scene=Scene(robot=NS(data=robot),box=NS(data=box))
    robot.body_com_pos_w = robot.body_pos_w
    scene.env_origins=torch.zeros(n,3)
    for side in ('left','right'):
        scene[side+'_box_contact']=NS(data=NS(force_matrix_w=torch.zeros(n,1,1,3)))
    return NS(scene=scene,common_step_counter=0,num_envs=n,device='cpu',
        _walled=NS(torso=3,head=0,hands=[1,2],arm_ids=[0,1],achieved=torch.zeros(n,dtype=torch.bool)))


class HandoffTests(unittest.TestCase):
    def test_standup_gate_is_instant_and_translation_invariant(self):
        env=fixture()
        terms=reward_terms(env)
        torch.testing.assert_close(terms['standup_task'],torch.full((4,),5.))
        self.assertFalse(env._walled.achieved.any()) # Does not fabricate strict contact+hold success.
        self.assertEqual(float(terms['walk_task'][0]),1.5)
        env.scene.env_origins[:,2]=7.
        env.scene['robot'].data.root_pos_w[:,2]+=7.
        env.scene['robot'].data.body_pos_w[:,:,2]+=7.
        env.scene['box'].data.root_pos_w[:,2]+=7.
        env.common_step_counter+=1
        for key,value in reward_terms(env).items():torch.testing.assert_close(value,terms[key],atol=2e-5,rtol=0)
        env.scene['robot'].data.body_pos_w[:,0,2]=7.8 # strict >0.8; stay just below boundary for float32
        env.scene['robot'].data.body_pos_w[:,0,2]-=.001
        env.common_step_counter+=1
        self.assertEqual(float(reward_terms(env)['standup_task'].sum()),0.)

    def test_hand_force_units_and_pickup_gates(self):
        env=fixture();robot=env.scene['robot'].data;box=env.scene['box'].data
        robot.root_pos_w[:,2]=.55;box.root_pos_w[:,2]=.5;robot.body_pos_w[:,1:3,2]=.5
        robot.joint_vel[:]=torch.tensor([2.,0.]);robot.joint_acc[:]=torch.tensor([30.,0.])
        env.scene['left_box_contact'].data.force_matrix_w[:,0,0,2]=7.
        env.scene['right_box_contact'].data.force_matrix_w[:,0,0,2]=9.
        terms=reward_terms(env)
        self.assertAlmostEqual(float(terms['grip_force_cap'][0]),1.)
        self.assertAlmostEqual(float(terms['arm_speed_pickup'][0]),.5)
        self.assertAlmostEqual(float(terms['arm_acc_pickup'][0]),50.)
        expected=.7+1.5*((1-math.exp(-3.5))+(1-math.exp(-4.5)))/2+1.5*math.exp(-.42)
        self.assertAlmostEqual(float(terms['carryup_task'][0]),expected,places=5)
        robot.body_pos_w[:,1:3,0]+=1.;env.common_step_counter+=1
        terms=reward_terms(env)
        self.assertEqual(float(terms['grip_force_cap'].sum()),0.)
        self.assertAlmostEqual(float(terms['carryup_task'][0]),.7*math.exp(-3)+1.5*math.exp(-.42),places=5)
        box.root_pos_w[:,0]=2.;env.common_step_counter+=1
        terms=reward_terms(env)
        for key in ('carryup_task','arm_speed_pickup','arm_acc_pickup','slow_pickup','stable_grasp'):
            self.assertEqual(float(terms[key].sum()),0.)

    def test_walk_uses_world_torso_velocity_and_roll_both_sides(self):
        env=fixture();robot=env.scene['robot'].data;box=env.scene['box'].data
        box.root_pos_w[:,0]=2.
        robot.body_lin_vel_w[0,3,0]=.85;robot.body_lin_vel_w[1,3,0]=-.85
        terms=reward_terms(env)
        self.assertAlmostEqual(float(terms['walk_task'][0]),1.5,places=6)
        self.assertLess(float(terms['walk_task'][1]),.501)
        z=torch.zeros(4);robot.root_quat_w=quat_from_euler_xyz(torch.tensor([.51,-.51,.49,-.49]),z,z)
        self.assertEqual(wall.tipped(env).tolist(),[True,True,False,False])
        robot.root_quat_w=quat_from_euler_xyz(z,torch.tensor([1.11,-1.11,1.,-1.]),z)
        self.assertEqual(wall.tipped(env).tolist(),[True,True,False,False])

    def test_noise_units_misses_holes_and_non_wrapping_edges(self):
        torch.manual_seed(7)
        d=torch.ones(100,27,48)
        d[:,0,:]=3.;d[:,1,0]=float('nan');d[:,1,1]=float('inf')
        noisy=corrupt_depth_m(d,edge_probability=0,hole_probability=0,stereo_near=0,stereo_far=0)
        self.assertTrue(torch.isfinite(noisy).all())
        self.assertTrue((noisy[:,0,:]==3.).all());self.assertTrue((noisy[:,1,:2]==3.).all())
        self.assertAlmostEqual(float((noisy[:,2:]-1.).std()),.06,delta=.001)
        edge=torch.tensor([[[1.,1.,1.,2.,2.,2.]]])
        out=corrupt_depth_m(edge,gaussian_std=0,edge_probability=1,hole_probability=0,stereo_near=0,stereo_far=0)
        torch.testing.assert_close(out,torch.tensor([[[1.,1.,3.,3.,2.,2.]]]))
        out=corrupt_depth_m(edge,hole_probability=1)
        self.assertTrue((out==3.).all())

    def test_exact_fifteen_frame_freeze_and_partial_reset(self):
        d=torch.zeros(2,2,3);p=torch.zeros(2,9);zero=torch.zeros(2,dtype=torch.long)
        b=PairedDepthBuffer(d,p,1);b.update(0,d,p,zero,zero)
        b.update(1,d+1,p+1,zero,torch.tensor([14,0]))
        for step in range(2,16):
            out,label=b.update(step,d+step,p+step,zero,zero)
            self.assertEqual(float(label[0,0]),1.)
            torch.testing.assert_close(out[:,0,0],label[:,0])
        out,label=b.update(16,d+16,p+16,zero,zero)
        self.assertEqual(float(label[0,0]),16.)
        old=out.clone();b.update(16,d+99,p+99,zero,zero);torch.testing.assert_close(b.output_depth,old)
        b.reset(torch.tensor([0]));out,label=b.update(16,d+20,p+20,torch.ones(2,dtype=torch.long),zero)
        self.assertEqual(float(label[0,0]),20.);self.assertEqual(float(label[1,0]),16.)

    def test_defaults_and_bounded_push_write_real_targets(self):
        env=fixture();robot=env.scene['robot']
        robot.data.default_joint_pos=torch.zeros(4,29)
        action=NS(_offset=torch.zeros(4,29),_joint_ids=slice(None))
        env.action_manager=NS(get_term=lambda name:action)
        wall.randomize_default_joint_pos(env,torch.tensor([1,3]))
        torch.testing.assert_close(action._offset,robot.data.default_joint_pos)
        self.assertLessEqual(float(action._offset.abs().max()),.01)
        self.assertEqual(float(action._offset[[0,2]].abs().sum()),0.)
        calls=[];robot.write_root_velocity_to_sim=lambda value,env_ids:calls.append(value)
        ranges={k:(-.2,.2) for k in ('x','y','z','roll','pitch','yaw')}
        for _ in range(3):wall.push_velocity(env,torch.arange(4),ranges)
        self.assertTrue(all((v.abs()<=.2).all() for v in calls))

    def test_new_dataset_pickup_action_coverage_including_default_error(self):
        path=Path(DEFAULT_DATASET_PATH);manifest=json.loads((path/'amp_manifest.json').read_text())
        source=path.parents[1]/'robots/g1_29dof.py'
        tree=ast.parse(source.read_text())
        defaults=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.keyword) and n.arg=='joint_pos')
        nominal=torch.tensor([next(v for pattern,v in defaults.items() if re.fullmatch(pattern,name)) for name in manifest['joint_names']])
        for clip in manifest['clips']:
            joints=torch.load(path/clip['file'],weights_only=True)['joint_position']
            bound=((joints-nominal).abs()+.01)/.25
            self.assertLessEqual(float(bound.max()),9.,clip['file'])


if __name__=='__main__':unittest.main()
