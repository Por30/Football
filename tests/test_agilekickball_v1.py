"""New gradual-speed contract; old strict-window tests are archived in docs."""
import copy
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import torch
import test_soccer_v3 as fixtures
from test_agilekickball_learning import LearningTests, ContinuousRoundTests, SpeedCurriculumTests, SoccerTests
from test_agile_play_course import PlayCourseTests
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball import AgileKickballState, exposure_speed_curriculum
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v1 import AgileKickballV1State, incoming_speed_curriculum
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner


class V1Tests(unittest.TestCase):
    def state(self, n=2, **kw):
        env,_=fixtures.state_fixture(n)
        kb=AgileKickballV1State(env,**kw);env._kickball=kb;kb.reset(torch.arange(n))
        return env,kb

    def tick(self,env,kb,n=1):
        for _ in range(n):env.common_step_counter+=1;kb.tick()

    def test_v0_bootstrap_and_piecewise_boundaries(self):
        env,kb=self.state()
        v0env,_=fixtures.state_fixture();v0=AgileKickballState(v0env);v0env._kickball=v0
        cases=[(0,.8),(60000,1.1),(239999,.8+1.2*239999/240000),
               (240000,2.),(240001,2.+3./240000),(360000,3.5),(480000,5.),(999999,5.)]
        before=env.scene['ball'].data.root_lin_vel_w.clone()
        for e,upper in cases:
            kb.exposure_offset=e;incoming_speed_curriculum(env,None)
            self.assertAlmostEqual(kb.serve_speed_range[1],upper)
            self.assertEqual(kb.serve_speed_range[0],.4)
            v0.exposure_offset=e;exposure_speed_curriculum(v0env,None)
            self.assertEqual(kb.serve_distance_range,v0.serve_distance_range)
            if e<=240000:self.assertEqual(kb.serve_speed_range,v0.serve_speed_range)
        torch.testing.assert_close(before,env.scene['ball'].data.root_lin_vel_w)

    def test_no_incoming_no_progress_and_tick_is_idempotent(self):
        env,kb=self.state();kb.ball_active[:]=False;kb.wait_elapsed[:]=5.
        self.tick(env,kb,50);incoming_speed_curriculum(env,None)
        self.assertEqual(kb.exposure_steps,0.);self.assertEqual(kb.serve_speed_range,(.4,.8))
        kb.ball_active[:]=True
        env.scene['ball'].data.root_pos_w[:]=torch.tensor([.6,0,.11])
        env.scene['ball'].data.root_lin_vel_w[:]=torch.tensor([-.4,0,0])
        self.tick(env,kb);self.assertEqual(kb.exposure_steps,1.)
        kb.tick();self.assertEqual(kb.exposure_steps,1.)
        env.reset_buf[:]=True;self.tick(env,kb);self.assertEqual(kb.exposure_steps,1.)

    def test_uniform_sampling_and_environment_count_independence(self):
        torch.manual_seed(42)
        for n in [1,4096]:
            env,kb=self.state(n);kb.incoming_steps[:]=360000
            incoming_speed_curriculum(env,None)
            self.assertEqual(kb.serve_speed_range,(.4,3.5))
        speed=kb._sample_serve_speed(torch.arange(4096))
        self.assertTrue(((speed>=.4)&(speed<=3.5)).all())
        self.assertAlmostEqual(speed.mean().item(),1.95,delta=.05)
        self.assertAlmostEqual((speed<1.95).float().mean().item(),.5,delta=.04)
        data=kb.curriculum_state_dict();_,small=self.state(2);small.load_curriculum_state_dict(data)
        self.assertEqual(small.exposure_steps,360000.)
        self.assertEqual(small.serve_speed_range,(.4,3.5))
        self.assertEqual(small.incoming_steps.sum(),0.)

    def test_schema_and_exposure_validation(self):
        _,kb=self.state();data=kb.curriculum_state_dict()
        for value in [float('nan'),float('inf'),-1.,None,True]:
            bad=copy.deepcopy(data);bad['exposure_steps']=value
            with self.assertRaises(ValueError):kb.load_curriculum_state_dict(bad)
        for key,value in [('schema',1),('config',{}),('schema',99)]:
            bad=copy.deepcopy(data);bad[key]=value
            with self.assertRaises(ValueError):kb.load_curriculum_state_dict(bad)
        for value in [0,-1,1.5,True]:
            with self.assertRaises(ValueError):self.state(extension_ramp_steps=value)
        kb.load_curriculum_state_dict(None);self.assertEqual(kb.serve_speed_range,(.4,.8))

    def test_joint_noise_does_not_block_but_body_conditions_do(self):
        env,kb=self.state();q=env.scene['robot'].data;q.joint_vel[:]=2.
        self.assertTrue(kb.balanced().all());self.assertFalse(AgileKickballState.balanced(kb).any())
        before=q.joint_vel.clone();robot_before=q.root_pos_w.clone()
        kb.ball_active[:]=False;kb.steps_since_ball_ended[:]=20
        self.tick(env,kb,22)
        self.assertEqual(int(kb.recovered_serves.sum()),2)
        torch.testing.assert_close(q.joint_vel,before);torch.testing.assert_close(q.root_pos_w,robot_before)
        cases=[('joint_vel',(slice(None),0),float('nan')),('joint_vel',(slice(None),0),float('inf')),
               ('projected_gravity_b',(slice(None),0),.2),('projected_gravity_b',(slice(None),2),1.),
               ('root_lin_vel_w',(slice(None),0),.3),('root_ang_vel_b',(slice(None),0),.6),
               ('root_pos_w',(slice(None),2),.6),('root_pos_w',(slice(None),2),1.),
               ('body_link_pos_w',(slice(None),slice(None),2),.13),
               ('body_link_pos_w',(slice(None),slice(None),2),-.04)]
        for attr,index,value in cases:
            with self.subTest(condition=(attr,value)):
                env,kb=self.state();getattr(env.scene['robot'].data,attr)[index]=value
                kb.ball_active[:]=False;kb.steps_since_ball_ended[:]=20
                self.tick(env,kb,22)
                self.assertFalse(kb.balanced().any());self.assertEqual(int(kb.recovered_serves.sum()),0)

    def runner(self,env):
        alg,_=fixtures.make_algorithm();r=BallRegressionOnPolicyRunner.__new__(BallRegressionOnPolicyRunner)
        r.alg=alg;r.device='cpu';r.env=NS(unwrapped=env);r.current_learning_iteration=1
        r.logger_type='tensorboard';r.disable_logs=True
        return r

    def test_runner_roundtrip_frozen_play_and_resume(self):
        env,kb=self.state();r=self.runner(env);kb.exposure_offset=360000.
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/'model.pt');r.save(path)
            payload=torch.load(path,weights_only=False)
            self.assertIn('agile_speed_curriculum',payload);self.assertNotIn('agile_success_curriculum',payload)
            kb.exposure_offset=0.;r.load(path,load_optimizer=False)
            self.assertFalse(kb.curriculum_training);self.assertEqual(kb.serve_speed_range,(.4,3.5))
            before=kb.curriculum_state_dict()
            kb.incoming_steps[:]=900000
            for _ in range(3):incoming_speed_curriculum(env,None);kb.reset(torch.arange(2))
            self.assertEqual(before,kb.curriculum_state_dict());self.assertEqual(kb.serve_speed_range,(.4,3.5))
            r.load(path,load_optimizer=True);self.assertTrue(kb.curriculum_training)
            kb.incoming_steps[:]=120000;incoming_speed_curriculum(env,None)
            self.assertEqual(kb.serve_speed_range,(.4,5.))

    def test_old_strict_rejected_and_v0_exposure_migrates(self):
        env,kb=self.state();r=self.runner(env)
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/'model.pt');r.save(path);state=torch.load(path,weights_only=False)
            del state['agile_speed_curriculum'];state['agile_success_curriculum']={'schema':1}
            torch.save(state,path)
            for optimizer in [False,True]:
                with self.assertRaisesRegex(ValueError,'Old strict-success'):r.load(path,load_optimizer=optimizer)
            del state['agile_success_curriculum'];state['agile_incoming_exposure_steps']=145500.
            torch.save(state,path);r.load(path,load_optimizer=False)
            self.assertEqual(kb.exposure_steps,145500.);self.assertAlmostEqual(kb.serve_speed_range[1],1.5275)


class V1RecoveryTests(ContinuousRoundTests):
    def setup_state(self):
        return V1Tests().state()


if __name__=='__main__':unittest.main()
