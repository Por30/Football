"""Round attribution, recovery timing, non-stalling sampling and checkpoint contracts."""
import copy
import tempfile
from pathlib import Path
import unittest
import torch
import test_agilekickball_v1 as previous
import test_play_ballspeed as play_checks
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v2 import (AgileKickballV2State, recovery_timed_out, active_kick_bonus, stable_return_bonus, failed_episode, stable_return_speed, stand_until_kick_window)


class V2Tests(unittest.TestCase):
    runner = previous.V1Tests.runner
    tick = previous.V1Tests.tick

    def state(self, n=2):
        env, _ = previous.fixtures.state_fixture(n)
        env.scene['robot'].data.body_link_lin_vel_w = torch.zeros(n, 2, 3)
        kb = AgileKickballV2State(env);env._kickball = kb;kb.reset(torch.arange(n))
        return env, kb

    def set_course(self, kb, steps):
        data = kb.curriculum_state_dict();data['control_steps'] = steps;kb.load_curriculum_state_dict(data)

    def strike(self, env, kb, active=True):
        ball, robot = env.scene['ball'].data, env.scene['robot'].data
        ball.root_pos_w[:] = torch.tensor([.2, 0., .11])
        ball.root_lin_vel_w[:] = torch.tensor([1., 0., 0.])
        robot.body_link_lin_vel_w[:, :, 0] = 1. if active else 0.
        self.tick(env, kb)

    def end_return(self, env, kb):
        env.scene['ball'].data.root_pos_w[:] = torch.tensor([3.1, 0., .11])
        self.tick(env, kb)

    def assert_ledger(self, kb):
        self.assertEqual(kb.serves.sum().item(), (kb.closed.sum()+kb.censored.sum()+kb.round_open.sum()).item())
        self.assertTrue((kb.joint_success <= kb.closed).all())
        self.assertTrue((kb.cdf_success <= kb.joint_success[:, None]).all())

    def test_control_clock_boundaries_waiting_and_environment_count(self):
        for n in [1, 4096]:
            env, kb = self.state(n)
            for steps, upper in [(0,.8),(120000,.8),(360000,2.),(720000,5.),(840000,6.),(1200000,6.)]:
                self.set_course(kb,steps)
                self.assertAlmostEqual(kb.serve_speed_range[1],upper)
            self.assertAlmostEqual(kb.serve_distance_range[0],.5)
            self.assertAlmostEqual(kb.serve_distance_range[1],2.26)
            self.set_course(kb,360000);kb.ball_active[:] = False;kb.recovery_elapsed[:] = 5.;kb.recovering[:] = True
            self.tick(env,kb,5)
            self.assertEqual(kb.course_steps,360005)
            kb.tick();self.assertEqual(kb.course_steps,360005)
            before=kb.course_steps;kb.reset(torch.tensor([0]));kb._sync_course();self.assertEqual(kb.course_steps,before)

    def test_no_success_still_samples_above_five_and_override(self):
        torch.manual_seed(42);env,kb=self.state(4096);self.set_course(kb,840000)
        samples=kb._sample_serve_speed(torch.arange(4096))
        self.assertTrue(((samples>=.4)&(samples<=6.)).all())
        self.assertAlmostEqual((samples>5.).float().mean().item(),.05 + .10/5.6,delta=.025)
        self.assertAlmostEqual(((samples>1.) & (samples<5.)).float().mean().item(),.10*4./5.6,delta=.025)
        self.assertAlmostEqual(kb._teacher()[0].item(),.4)
        kb.serve_speed_override=(5.5,5.5);kb._sync_course()
        torch.testing.assert_close(kb._sample_serve_speed(torch.arange(4096)),torch.full((4096,),5.5))
        self.assertEqual(kb.serve_speed_range,(5.5,5.5))

    def test_mastery_contiguous_and_batch_ema_order_independent(self):
        _,kb=self.state(4);kb.train_closed[:]=128;kb.train_ema[:]=.9
        kb.train_ema[1]=.6
        self.assertEqual(kb._teacher()[0].item(),1.)
        kb.train_ema[1]=.9;self.assertEqual(kb._teacher()[0].item(),6.)
        _,a=self.state(4);_,b=self.state(4)
        for state,order in [(a,torch.arange(4)),(b,torch.tensor([3,1,0,2]))]:
            state.round_bin[:]=torch.tensor([0,1,0,1]);state.strict_candidate[:]=torch.tensor([1,1,0,0]).bool()
            state.returned[:]=True;state.first_ready_s[:]=.3;state._settle(order,recovered=True)
        torch.testing.assert_close(a.train_ema,b.train_ema)
        torch.testing.assert_close(a.train_closed,torch.tensor([2,2,0,0,0,0]))
        expected=.5*(1.-torch.exp(torch.tensor(-2./512.)))
        torch.testing.assert_close(a.train_ema[0],expected)

    def test_strike_then_ball_end_recovery_cooldown_and_conservation(self):
        env,kb=self.state();self.strike(env,kb)
        self.assertTrue(kb.strict_candidate.all());self.assertTrue(kb.recovering.all())
        self.assertEqual(kb.recovery_elapsed.sum(),0.)
        self.tick(env,kb,16)
        self.assertTrue(kb.ball_active.all());self.assertTrue((kb.first_ready_s<0).all())
        self.assertEqual(kb.recovered_serves.sum(),0)
        prior=kb.recovery_elapsed.clone();env.scene['ball'].data.root_lin_vel_w[:,0]=1.5
        self.tick(env,kb);self.assertTrue((kb.recovery_elapsed>prior).all())
        self.end_return(env,kb);self.assertTrue(kb.returned.all())
        self.tick(env,kb,18);self.assertEqual(kb.recovered_serves.sum(),0)
        robot_before=env.scene['robot'].data.root_pos_w.clone()
        self.tick(env,kb);self.assertEqual(kb.recovered_serves.sum(),0)
        self.tick(env,kb)
        self.assertEqual(kb.recovered_serves.sum(),2);self.assertEqual(kb.joint_success.sum(),2)
        self.assertEqual(kb.cdf_success[:,0].sum(),0);self.assertEqual(kb.cdf_success[:,1].sum(),2)
        self.assertTrue((kb.streak==1).all())
        self.assertTrue(stable_return_bonus(env).bool().all())
        kb.tick();self.assertTrue(stable_return_bonus(env).bool().all())
        self.tick(env,kb);self.assertEqual(stable_return_bonus(env).sum(),0)
        torch.testing.assert_close(robot_before,env.scene['robot'].data.root_pos_w)
        self.assert_ledger(kb)
        kb.reset(torch.tensor([0]));self.assertEqual(kb.censored.sum(),1);self.assert_ledger(kb)
        kb.reset(torch.tensor([0]));self.assertEqual(kb.censored.sum(),2);self.assert_ledger(kb)

    def test_fixed_hold_despite_peak_interrupt_anchor_and_finite_guards(self):
        env,kb=self.state();q=env.scene['robot'].data
        q.root_lin_vel_w[:,0]=1.;self.tick(env,kb);self.assertTrue((kb.required_hold==.3).all())
        q.root_lin_vel_w.zero_();self.strike(env,kb);self.end_return(env,kb)
        kb._serve=lambda ids: None  # isolate stability tracking before physical re-serve
        self.tick(env,kb,12)
        self.assertTrue((kb.first_ready_s<0).all())
        q.root_lin_vel_w[:,0]=.3;self.tick(env,kb);self.assertEqual(kb.stable_elapsed.sum(),0)
        q.root_lin_vel_w.zero_();self.tick(env,kb,21);self.assertTrue((kb.first_ready_s>0).all())
        self.assertTrue((kb.required_hold==.3).all())
        previous_ready=kb.first_ready_s.clone()
        q.root_lin_vel_w[:,0]=.3;self.tick(env,kb)
        self.assertTrue((kb.first_ready_s<0).all())
        q.root_lin_vel_w.zero_();self.tick(env,kb,21)
        self.assertTrue((kb.first_ready_s>previous_ready).all())
        q.root_pos_w[:,0]=.6;self.assertFalse(kb.balanced().any())
        q.root_pos_w[:,0]=0.;q.joint_vel[:,0]=float('nan');self.assertFalse(kb.balanced().any())

    def test_timeout_only_after_ball_end_and_termination_wins_over_serve(self):
        env,kb=self.state();self.strike(env,kb);self.tick(env,kb,12)
        self.assertTrue((kb.first_ready_s<0).all())
        kb.recovery_elapsed[:]=10.
        self.assertTrue(kb.ball_active.all());self.assertFalse(recovery_timed_out(env).any())
        self.end_return(env,kb);self.assertFalse(recovery_timed_out(env).any())
        kb.wait_elapsed[:]=5.;self.assertTrue(recovery_timed_out(env).all())
        env.reset_buf[:]=True;self.tick(env,kb)
        self.assertEqual(kb.closed.sum(),2);self.assertEqual(kb.joint_success.sum(),0)
        self.assertEqual(kb.cdf_success.sum(),0);self.assertEqual(kb.recovered_serves.sum(),0)
        kb.reset(torch.arange(2));self.assertEqual(kb.censored.sum(),0);self.assert_ledger(kb)
        env.reset_buf[:]=False;self.strike(env,kb);self.end_return(env,kb)
        self.tick(env,kb,18);env.reset_buf[:]=True;self.tick(env,kb)
        self.assertEqual(kb.recovered_serves.sum(),0);self.assertEqual(kb.closed.sum(),4)

    def test_passive_bounce_and_miss_not_joint_success(self):
        env,kb=self.state();self.strike(env,kb,active=False)
        self.assertFalse(kb.ball_kicked.any());self.assertEqual(active_kick_bonus(env).sum(),0)
        self.assertEqual(stable_return_speed(env).sum(),0)
        self.end_return(env,kb);self.assertTrue(kb.just_missed.all())
        self.tick(env,kb,20)
        self.assertEqual(kb.recovered_serves.sum(),2);self.assertEqual(kb.joint_success.sum(),0)
        kb.streak[:]=3
        ball=env.scene['ball'].data;ball.root_pos_w[:,0]=-.4;ball.root_lin_vel_w[:,0]=-.5
        self.tick(env,kb);self.assertTrue(kb.recovering.all())
        self.tick(env,kb,20);self.assertEqual(kb.joint_success.sum(),0);self.assertEqual(kb.streak.sum(),0)
        self.assert_ledger(kb)

    def test_bins_and_teleport_does_not_create_return(self):
        env,kb=self.state(6)
        self.assertEqual(torch.bucketize(torch.tensor([.4,1.,2.,3.,4.,5.]),kb.bin_edges,right=True).tolist(),list(range(6)))
        self.strike(env,kb);env.scene['ball'].data.root_lin_vel_w.zero_()
        self.tick(env,kb);self.tick(env,kb,20)
        self.assertEqual(kb.recovered_serves.sum(),6);self.assertEqual(kb.joint_success.sum(),0)
        self.assert_ledger(kb)

    def test_checkpoint_resume_freeze_and_rejection_before_weights(self):
        env,kb=self.state();r=self.runner(env);self.set_course(kb,720000)
        kb.train_closed[:]=128;kb.train_ema[:]=.8
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/'v2.pt');r.save(path)
            saved=kb.curriculum_state_dict();self.set_course(kb,0)
            r.load(path,load_optimizer=False);self.assertFalse(kb.curriculum_training)
            self.strike(env,kb);self.end_return(env,kb);self.tick(env,kb,20)
            kb.reset(torch.arange(2));self.assertEqual(saved,kb.curriculum_state_dict())
            kb.serve_speed_override=(6.,6.);kb._sync_course();kb.reset(torch.arange(2))
            self.assertEqual(kb.serve_speed_range,(6.,6.))
            kb.serve_speed_override=None
            r.load(path,load_optimizer=True);self.tick(env,kb,3);self.assertEqual(kb.course_steps,720003)
            r.load(path,load_optimizer=True);self.assertEqual(kb.course_steps,720000)
            original=torch.load(path,weights_only=False)
            for change in [('schema',2),('schema',3),('control_steps',True),('control_steps',-1),('exposure_steps',float('nan')),
                           ('train_closed',[1]*5),('train_ema',[float('inf')]*6),('train_ema',[-.1]*6),('config',{})]:
                bad=copy.deepcopy(original);bad[kb.curriculum_checkpoint_key][change[0]]=change[1];bad['model_state_dict']={}
                torch.save(bad,path)
                with self.assertRaises(ValueError):r.load(path)
            bad=copy.deepcopy(original);del bad[kb.curriculum_checkpoint_key];bad['model_state_dict']={};torch.save(bad,path)
            with self.assertRaisesRegex(ValueError,'v2 recovery'):r.load(path,load_optimizer=False)

    def test_sampled_speed_drives_distance_once_and_partial_ids(self):
        env,kb=self.state(128);self.set_course(kb,840000)
        ids=torch.tensor([1,7,19,127]);others=torch.tensor([0,2,18,126])
        for speed in [.4,.8,1.45,6.]:
            kb.serve_speed_override=(speed,speed)
            before=kb.sampled.sum().clone();untouched=env.scene['ball'].data.root_pos_w[others].clone()
            kb.reset(ids)
            self.assertEqual(kb.sampled.sum()-before,len(ids))
            actual_speed=env.scene['ball'].data.root_lin_vel_w[ids,:2].norm(dim=-1)
            torch.testing.assert_close(actual_speed,torch.full_like(actual_speed,speed))
            dist=(env.scene['ball'].data.root_pos_w[ids,:2]-kb.anchor_xy[ids]).norm(dim=-1)
            extra=.3*min(max(speed-.8,0),5.2)
            self.assertTrue(((dist>=.5+extra-1.e-5)&(dist<=.7+extra+1.e-5)).all())
            torch.testing.assert_close(untouched,env.scene['ball'].data.root_pos_w[others])
            self.assertIsNone(kb._pending_serve_speed)
            self.assertIsInstance(kb.serve_distance_range[0],float)
            self.assert_ledger(kb)
        # A simulator exception must not retain the private cached sample/distance bounds.
        write=kb.ball.write_root_pose_to_sim
        kb.ball.write_root_pose_to_sim=lambda *a,**kw: (_ for _ in ()).throw(RuntimeError('write failed'))
        with self.assertRaisesRegex(RuntimeError,'write failed'):kb.reset(ids)
        self.assertIsNone(kb._pending_serve_speed);self.assertIsInstance(kb.serve_distance_range[0],float)
        kb.ball.write_root_pose_to_sim=write

    def test_reward_pulses_failure_type_and_far_standing(self):
        from types import SimpleNamespace as NS
        from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.rewards import stand_task
        env,kb=self.state();self.strike(env,kb)
        self.assertEqual(active_kick_bonus(env).sum(),2)
        self.tick(env,kb);self.assertEqual(active_kick_bonus(env).sum(),0)
        env.termination_manager=NS(terminated=torch.tensor([True,False]))
        env.reset_buf[:]=True  # second environment represents time-limit-only truncation
        torch.testing.assert_close(failed_episode(env),torch.tensor([1.,0.]))
        self.assertLess(100*.02 + (-400)*.02,0.)
        self.assertGreater(100*.02 + 400*.02,100*.02)
        env.reset_buf[:]=False;kb.ball_active[:]=True;kb.ball_kicked[:]=False
        kb.ball.data.root_pos_w[:,0]=1.2
        torch.testing.assert_close(stand_until_kick_window(env),stand_task(env,target_height=.8))
        kb.ball.data.root_pos_w[:,0]=.4
        torch.testing.assert_close(stand_until_kick_window(env),.25*stand_task(env,target_height=.8))



def load_tests(loader, tests, pattern):
    # Runner edit also exercises the existing v0/v1 and play contracts.
    tests.addTests(loader.loadTestsFromModule(previous))
    tests.addTests(loader.loadTestsFromTestCase(play_checks.BallSpeedTests))
    return tests


if __name__=='__main__':unittest.main()
