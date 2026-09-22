"""Production v1 state/runner tests with explicit physics boundary doubles."""
import copy
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import torch
import test_soccer_v3 as fixtures
from test_agilekickball_learning import LearningTests, ContinuousRoundTests, SpeedCurriculumTests, SoccerTests
from test_agile_play_course import PlayCourseTests
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v1 import AgileKickballV1State, STAGE_UPPERS
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner


class V1Tests(unittest.TestCase):
    def state(self,n=2,**kw):
        env,_=fixtures.state_fixture(n)
        env.scene['robot'].data.body_link_lin_vel_w=torch.zeros(n,2,3)
        kb=AgileKickballV1State(env,**kw);env._kickball=kb;kb.reset(torch.arange(n))
        return env,kb

    def tick(self,env,kb,n=1):
        for _ in range(n):env.common_step_counter+=1;kb.tick()

    def contact(self,env,kb,active=True):
        ball=env.scene['ball'].data
        ball.root_pos_w[:]=torch.tensor([.2,0.,.11]);ball.root_lin_vel_w[:]=torch.tensor([1.,0.,0.])
        env.scene['robot'].data.body_link_lin_vel_w[:,:,0]=1. if active else 0.
        self.tick(env,kb)

    def end_and_recover(self,env,kb):
        env.scene['ball'].data.root_pos_w[:]=torch.tensor([.8,0.,.11])
        env.scene['ball'].data.root_lin_vel_w[:]=torch.tensor([.1,0.,0.])
        env.scene['robot'].data.body_link_lin_vel_w.zero_()
        self.tick(env,kb);self.tick(env,kb,22)

    def test_active_kick_progress_then_recovery_settles_once(self):
        env,kb=self.state();before=env.scene['robot'].data.root_pos_w.clone()
        self.contact(env,kb)
        self.assertTrue(kb.candidate.all());self.assertEqual(kb.settled_total,0)
        self.end_and_recover(env,kb)
        self.assertEqual(kb.settled_total,2);self.assertEqual(kb.strict_success_total,2)
        self.assertEqual(kb.window['total'],2);self.assertTrue(kb.round_open.all())
        self.assertEqual(int(kb.recovered_serves.sum()),2)
        torch.testing.assert_close(before,env.scene['robot'].data.root_pos_w)
        kb.tick();self.assertEqual(kb.settled_total,2)

    def test_passive_rebound_not_course_success(self):
        env,kb=self.state();self.contact(env,kb,active=False)
        self.assertTrue(kb.kick_success_flag.all())  # v0 reward semantics retained
        self.assertFalse(kb.candidate.any());self.end_and_recover(env,kb)
        self.assertEqual(kb.strict_success_total,0);self.assertEqual(kb.window['total'],2)

    def test_termination_partial_reset_and_no_double_count(self):
        env,kb=self.state();self.contact(env,kb)
        kb.returned[:]=True;env.reset_buf[0]=True
        self.tick(env,kb);self.assertEqual(kb.settled_total,1);self.assertEqual(kb.strict_success_total,0)
        kb.reset(torch.tensor([0]));self.assertEqual(kb.settled_total,1)
        self.assertTrue(kb.round_open.all())
        self.assertTrue(kb.candidate[1]);self.assertFalse(kb.candidate[0])
        env.reset_buf[:]=False
        kb.reset(torch.tensor([1]));self.assertEqual(kb.settled_total,2)

    def test_progress_is_projection_not_teleport_or_lateral_motion(self):
        env,kb=self.state();self.contact(env,kb)
        env.scene['ball'].data.root_pos_w[:,1]=1.
        self.tick(env,kb);self.assertFalse(kb.returned.any())
        kb.reset(torch.arange(2));self.assertFalse(kb.candidate.any());self.assertFalse(kb.returned.any())

    def test_two_disjoint_windows_challenge_and_dwell_guards(self):
        _,kb=self.state(window_size=10,min_challenge_count=2,required_windows=2,min_stage_steps=1000)
        good=dict(total=10,successes=8,challenge=4,challenge_successes=4)
        kb.window=good.copy();kb._advance_window();self.assertEqual(kb.stage,0)
        kb.window=good.copy();kb._advance_window();self.assertEqual(kb.stage,0)  # no dwell
        kb.stage_steps=1000
        kb.window=dict(total=10,successes=8,challenge=2,challenge_successes=0)
        kb._advance_window();self.assertEqual(kb.passing_windows,0)
        for _ in range(2):kb.window=good.copy();kb._advance_window()
        self.assertEqual(kb.stage,1);self.assertEqual(kb.window['total'],0);self.assertEqual(kb.stage_steps,0)
        kb.round_stage[:]=0;kb._settle(torch.arange(2),torch.ones(2,dtype=torch.bool))
        self.assertEqual(kb.window['total'],0);self.assertEqual(kb.settled_total,2)

    def test_all_stage_sampling_and_cap(self):
        _,kb=self.state(2000)
        for stage,upper in enumerate(STAGE_UPPERS):
            kb.stage=stage;kb._sync_course();speed=kb._sample_serve_speed(torch.arange(2000))
            self.assertTrue(((speed>=.4)&(speed<=upper)).all())
            if stage:
                self.assertTrue((speed[kb.round_challenge]>=STAGE_UPPERS[stage-1]).all())
                self.assertTrue((speed[~kb.round_challenge]<=STAGE_UPPERS[stage-1]).all())
                self.assertGreater(int(kb.round_challenge.sum()),700)
                self.assertLess(int(kb.round_challenge.sum()),1300)
            else:self.assertTrue(kb.round_challenge.all())
        kb.stage_steps=10000
        for _ in range(3):
            kb.window=dict(total=4096,successes=4096,challenge=2048,challenge_successes=2048);kb._advance_window()
        self.assertEqual(kb.stage,9);self.assertEqual(kb.serve_speed_range,(.4,5.))

    def test_checkpoint_schema_validation_and_no_physics_restore(self):
        _,kb=self.state();kb.stage=5;kb.stage_steps=123;kb.window=dict(total=9,successes=5,challenge=4,challenge_successes=2)
        data=kb.curriculum_state_dict();kb.load_curriculum_state_dict(data)
        self.assertEqual(kb.stage,5);self.assertEqual(kb.stage_steps,123);self.assertFalse(kb.round_open.any())
        self.assertEqual(kb.truncated_on_load,2)
        for key,value in [('stage',99),('schema',2),('stage_steps',-1)]:
            bad=copy.deepcopy(data);bad[key]=value
            with self.assertRaises(ValueError):kb.load_curriculum_state_dict(bad)
        bad=copy.deepcopy(data);bad['window']['challenge_successes']=99
        with self.assertRaises(ValueError):kb.load_curriculum_state_dict(bad)
        kb.load_curriculum_state_dict(None);self.assertEqual(kb.stage,0)

    def test_runner_inference_restores_v1_and_freezes_progress(self):
        env,kb=self.state();alg,_=fixtures.make_algorithm()
        r=BallRegressionOnPolicyRunner.__new__(BallRegressionOnPolicyRunner)
        r.alg=alg;r.device='cpu';r.env=NS(unwrapped=env);r.current_learning_iteration=1;r.logger_type='tensorboard';r.disable_logs=True
        kb.stage=4;kb.stage_steps=1200;kb.window=dict(total=100,successes=80,challenge=50,challenge_successes=40)
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/'model.pt');r.save(path);kb.stage=0
            r.load(path,load_optimizer=False)
            self.assertEqual(kb.stage,4);self.assertEqual(kb.serve_speed_range,(.4,2.5))
            saved=kb.curriculum_state_dict();kb.reset(torch.arange(2));self.contact(env,kb);self.end_and_recover(env,kb)
            now=kb.curriculum_state_dict()
            for key in ('stage','stage_steps','passing_windows','window','last_window'):self.assertEqual(saved[key],now[key])
            r.load(path,load_optimizer=True);self.assertTrue(kb.curriculum_training)

if __name__=='__main__':unittest.main()
