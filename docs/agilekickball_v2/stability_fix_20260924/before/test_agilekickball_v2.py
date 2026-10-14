"""Round attribution, recovery timing, non-stalling sampling and checkpoint contracts."""
import copy
import tempfile
from pathlib import Path
import unittest
import torch
import test_agilekickball_v1 as previous
import test_play_ballspeed as play_checks
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v2 import AgileKickballV2State, recovery_timed_out


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
            self.assertEqual(kb.serve_distance_range,(2.,2.5))
            self.set_course(kb,360000);kb.ball_active[:] = False;kb.recovery_elapsed[:] = 5.;kb.recovering[:] = True
            self.tick(env,kb,5)
            self.assertEqual(kb.course_steps,360005)
            kb.tick();self.assertEqual(kb.course_steps,360005)
            before=kb.course_steps;kb.reset(torch.tensor([0]));kb._sync_course();self.assertEqual(kb.course_steps,before)

    def test_no_success_still_samples_above_five_and_override(self):
        torch.manual_seed(42);env,kb=self.state(4096);self.set_course(kb,840000)
        samples=kb._sample_serve_speed(torch.arange(4096))
        self.assertTrue(((samples>=.4)&(samples<=6.)).all())
        self.assertAlmostEqual((samples>5.).float().mean().item(),.25 + .2/5.6,delta=.04)
        self.assertGreater(((samples>1.) & (samples<5.)).sum().item(),300)
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

    def test_strike_parallel_recovery_cooldown_and_conservation(self):
        env,kb=self.state();self.strike(env,kb)
        self.assertTrue(kb.strict_candidate.all());self.assertTrue(kb.recovering.all())
        self.assertEqual(kb.recovery_elapsed.sum(),0.)
        self.tick(env,kb,16)
        self.assertTrue(kb.ball_active.all());self.assertTrue((kb.first_ready_s>0).all())
        self.assertEqual(kb.recovered_serves.sum(),0)
        prior=kb.recovery_elapsed.clone();env.scene['ball'].data.root_lin_vel_w[:,0]=1.5
        self.tick(env,kb);self.assertTrue((kb.recovery_elapsed>prior).all())
        self.end_return(env,kb);self.assertTrue(kb.returned.all())
        self.tick(env,kb,18);self.assertEqual(kb.recovered_serves.sum(),0)
        robot_before=env.scene['robot'].data.root_pos_w.clone()
        self.tick(env,kb)
        self.assertEqual(kb.recovered_serves.sum(),2);self.assertEqual(kb.joint_success.sum(),2)
        self.assertEqual(kb.cdf_success[:,0].sum(),2);self.assertTrue((kb.streak==1).all())
        torch.testing.assert_close(robot_before,env.scene['robot'].data.root_pos_w)
        self.assert_ledger(kb)
        kb.reset(torch.tensor([0]));self.assertEqual(kb.censored.sum(),1);self.assert_ledger(kb)
        kb.reset(torch.tensor([0]));self.assertEqual(kb.censored.sum(),2);self.assert_ledger(kb)

    def test_hold_peak_interrupt_anchor_and_finite_guards(self):
        env,kb=self.state();q=env.scene['robot'].data
        q.root_lin_vel_w[:,0]=1.;self.tick(env,kb);self.assertTrue((kb.required_hold==.4).all())
        q.root_lin_vel_w.zero_();self.strike(env,kb);self.tick(env,kb,12)
        self.assertTrue((kb.first_ready_s<0).all())
        q.root_lin_vel_w[:,0]=.3;self.tick(env,kb);self.assertEqual(kb.stable_elapsed.sum(),0)
        q.root_lin_vel_w.zero_();self.tick(env,kb,21);self.assertTrue((kb.first_ready_s>0).all())
        self.assertTrue((kb.required_hold==.4).all())
        previous_ready=kb.first_ready_s.clone()
        q.root_lin_vel_w[:,0]=.3;self.tick(env,kb)
        self.assertTrue((kb.first_ready_s<0).all())
        q.root_lin_vel_w.zero_();self.tick(env,kb,21)
        self.assertTrue((kb.first_ready_s>previous_ready).all())
        q.root_pos_w[:,0]=.6;self.assertFalse(kb.balanced().any())
        q.root_pos_w[:,0]=0.;q.joint_vel[:,0]=float('nan');self.assertFalse(kb.balanced().any())

    def test_timeout_active_and_termination_wins_over_serve(self):
        env,kb=self.state();self.strike(env,kb);self.tick(env,kb,12)
        self.assertTrue((kb.first_ready_s>0).all())
        kb.recovery_elapsed[:]=4.99
        self.assertTrue(kb.ball_active.all());self.assertTrue(recovery_timed_out(env).all())
        env.reset_buf[:]=True;self.tick(env,kb)
        self.assertEqual(kb.closed.sum(),2);self.assertEqual(kb.joint_success.sum(),0)
        self.assertEqual(kb.cdf_success.sum(),0);self.assertEqual(kb.recovered_serves.sum(),0)
        kb.reset(torch.arange(2));self.assertEqual(kb.censored.sum(),0);self.assert_ledger(kb)
        env.reset_buf[:]=False;self.strike(env,kb);self.end_return(env,kb)
        self.tick(env,kb,18);env.reset_buf[:]=True;self.tick(env,kb)
        self.assertEqual(kb.recovered_serves.sum(),0);self.assertEqual(kb.closed.sum(),4)

    def test_passive_bounce_and_miss_not_joint_success(self):
        env,kb=self.state();self.strike(env,kb,active=False);self.end_return(env,kb);self.tick(env,kb,20)
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
            for change in [('schema',2),('control_steps',True),('control_steps',-1),('exposure_steps',float('nan')),
                           ('train_closed',[1]*5),('train_ema',[float('inf')]*6),('train_ema',[-.1]*6),('config',{})]:
                bad=copy.deepcopy(original);bad[kb.curriculum_checkpoint_key][change[0]]=change[1];bad['model_state_dict']={}
                torch.save(bad,path)
                with self.assertRaises(ValueError):r.load(path)
            bad=copy.deepcopy(original);del bad[kb.curriculum_checkpoint_key];bad['model_state_dict']={};torch.save(bad,path)
            with self.assertRaisesRegex(ValueError,'v2 recovery'):r.load(path,load_optimizer=False)


def load_tests(loader, tests, pattern):
    # Runner edit also exercises the existing v0/v1 and play contracts.
    tests.addTests(loader.loadTestsFromModule(previous))
    tests.addTests(loader.loadTestsFromTestCase(play_checks.BallSpeedTests))
    return tests


if __name__=='__main__':unittest.main()
