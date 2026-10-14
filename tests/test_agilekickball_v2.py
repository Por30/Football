"""Speed-only v2 contract, plus unchanged v1 learning/recovery/play regressions."""
import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import torch
import test_agilekickball_v1 as previous
import test_play_ballspeed as play_checks
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v1 import AgileKickballV1State
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v2 import AgileKickballV2State


class V2Tests(unittest.TestCase):
    runner = previous.V1Tests.runner
    tick = previous.V1Tests.tick

    def state(self, n=2):
        env, _ = previous.fixtures.state_fixture(n)
        kb = AgileKickballV2State(env);env._kickball = kb;kb.reset(torch.arange(n));kb._window_counts=kb._counts()
        return env, kb

    def window(self, env, kb, recovery=.9, kick=.7, served=200, steps=6000):
        kb.serves[0] += served;kb.recovered_serves[0] += int(served*recovery)
        kb.successes[0] += int(served*kick)
        env.common_step_counter += steps;kb._sync_course()

    def unlock(self, env, kb):
        kb.exposure_offset=60000.;self.window(env,kb)
        self.assertTrue(kb.extension_unlocked)
        self.assertAlmostEqual(kb.serve_speed_range[1],1.1)

    def test_inherited_physical_methods(self):
        for name in ('tick','reset','_serve','_sample_serve_speed','_ready_to_serve','balanced','observation_status'):
            self.assertIs(getattr(AgileKickballV2State,name),getattr(AgileKickballV1State,name),name)

    def test_bootstrap_exact_v1_ranges_serve_and_rng(self):
        env,kb=self.state(16);oldenv,old=previous.V1Tests().state(16)
        for exposure in (0.,60000.,180000.,240000.):
            for state in (kb,old):state.exposure_offset=exposure;state._sync_course()
            self.assertEqual(kb.serve_speed_range,old.serve_speed_range)
            self.assertEqual(kb.serve_distance_range,old.serve_distance_range)
            torch.manual_seed(42);kb.reset(torch.arange(16));rng=torch.get_rng_state()
            torch.manual_seed(42);old.reset(torch.arange(16))
            torch.testing.assert_close(torch.get_rng_state(),rng,rtol=0,atol=0)
            for key in ('root_pos_w','root_lin_vel_w'):
                torch.testing.assert_close(getattr(env.scene['ball'].data,key),getattr(oldenv.scene['ball'].data,key),rtol=0,atol=0)

    def test_no_recovery_never_unlocks_even_after_long_time(self):
        env,kb=self.state();kb.exposure_offset=900000.
        self.window(env,kb,recovery=0.,kick=1.,steps=1200000)
        self.assertFalse(kb.extension_unlocked);self.assertEqual(kb.serve_speed_range,(.4,2.))
        self.assertEqual(kb.advance_rate,0.)

    def test_all_unlock_requirements_and_no_retroactive_progress(self):
        for exposure,recovery,kick,served in [(59999,.9,.9,200),(60000,.79,.9,200),
                                             (60000,.9,.59,200),(60000,.9,.9,100)]:
            env,kb=self.state();kb.exposure_offset=exposure
            self.window(env,kb,recovery,kick,served)
            self.assertFalse(kb.extension_unlocked)
        env,kb=self.state();self.unlock(env,kb)
        self.assertEqual(kb.extension_steps,0.);self.assertEqual(kb.advance_rate,1.)
        before=kb.curriculum_state_dict();kb._sync_course();kb.metrics()
        self.assertEqual(before,kb.curriculum_state_dict())

    def test_progress_pause_no_data_endpoint_and_uniform_sampling(self):
        env,kb=self.state(4096);self.unlock(env,kb)
        start=kb.course_steps
        # Bootstrap reset samples are included only in the first window.
        self.window(env,kb,recovery=.9,kick=.7,served=200)
        self.assertGreater(kb.extension_steps,0)
        self.window(env,kb,recovery=.4,kick=.7)
        self.assertEqual(kb.advance_rate,0.)
        frozen=kb.course_upper
        self.window(env,kb,recovery=.4,kick=.7)
        self.assertEqual(kb.course_upper,frozen)
        self.window(env,kb,recovery=.9,kick=.7)
        self.window(env,kb,served=0)
        self.assertEqual(kb.advance_rate,0.)
        frozen=kb.course_upper;self.window(env,kb,served=0)
        self.assertEqual(kb.course_upper,frozen)
        self.window(env,kb,recovery=.9,kick=.7)
        for _ in range(48):self.window(env,kb,recovery=.9,kick=.7)
        self.assertEqual(kb.course_upper,6.)
        torch.manual_seed(42);samples=kb._sample_serve_speed(torch.arange(4096))
        self.assertTrue(((samples>=.4)&(samples<=6.)).all())
        self.assertAlmostEqual(samples.mean().item(),3.2,delta=.08)
        self.assertAlmostEqual((samples>5.).float().mean().item(),1/5.6,delta=.025)
        self.assertGreater(kb.course_steps,start)

    def test_half_rate_and_no_kick_pause(self):
        env,kb=self.state();self.unlock(env,kb)
        self.window(env,kb,recovery=.65,kick=.6)
        self.assertAlmostEqual(kb.advance_rate,.5)
        prior=kb.extension_steps;self.window(env,kb,recovery=.9,kick=0.)
        self.assertAlmostEqual(kb.extension_steps-prior,3000.)
        self.assertEqual(kb.advance_rate,0.)

    def test_window_timing_and_logging_do_not_change_ranges(self):
        env,kb=self.state();kb.exposure_offset=60000.
        self.window(env,kb,steps=5999);self.assertFalse(kb.extension_unlocked)
        env.common_step_counter+=1;kb.metrics();self.assertFalse(kb.extension_unlocked)
        kb._sync_course();self.assertTrue(kb.extension_unlocked)
        self.assertEqual(kb.extension_steps,0.)

    def test_cross_environment_resume_preserves_course_not_old_window(self):
        env,kb=self.state(4096);self.unlock(env,kb);self.window(env,kb)
        data=kb.curriculum_state_dict();smallenv,small=self.state(1)
        small.load_curriculum_state_dict(data)
        self.assertEqual(small.curriculum_state_dict(),data)
        self.assertEqual(small.incoming_steps.sum(),0)
        self.window(smallenv,small,served=0)
        self.assertEqual(small.recent_serves,0);self.assertEqual(small.advance_rate,0.)
        small.load_curriculum_state_dict(data);self.assertEqual(small.curriculum_state_dict(),data)

    def test_checkpoint_play_freeze_override_resume_and_validation_before_weights(self):
        env,kb=self.state();self.unlock(env,kb);self.window(env,kb)
        runner=self.runner(env)
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/'v2.pt');runner.save(path);saved=kb.curriculum_state_dict()
            runner.load(path,load_optimizer=False);self.assertFalse(kb.curriculum_training)
            self.tick(env,kb,25);kb.reset(torch.arange(2));kb._sync_course()
            self.assertEqual(kb.curriculum_state_dict(),saved)
            kb.serve_speed_override=(6.,6.);kb._sync_course();kb.reset(torch.arange(2))
            self.assertEqual(kb.serve_speed_range,(6.,6.));self.assertEqual(kb.curriculum_state_dict(),saved)
            kb.serve_speed_override=None
            runner.load(path,load_optimizer=True);self.assertTrue(kb.curriculum_training)
            env.common_step_counter+=24;kb._sync_course()
            self.assertEqual(kb.course_steps,saved['control_steps']+24)
            original=torch.load(path,weights_only=False)
            for key,value in [('schema',3),('schema',4),('config',{}),('exposure_steps',float('nan')),
                ('control_steps',True),('control_steps',-1),('extension_steps',float('inf')),
                ('extension_steps',288001),('extension_start_upper',3.),('advance_rate',1.1),
                ('extension_unlocked',1),('recent_recovery_share',-1.)]:
                bad=copy.deepcopy(original);bad[kb.curriculum_checkpoint_key][key]=value;torch.save(bad,path)
                with patch.object(runner.alg.policy,'load_state_dict') as loader:
                    with self.assertRaises(ValueError):runner.load(path)
                    loader.assert_not_called()
            del original[kb.curriculum_checkpoint_key];torch.save(original,path)
            with patch.object(runner.alg.policy,'load_state_dict') as loader:
                with self.assertRaises(ValueError):runner.load(path)
                loader.assert_not_called()


class V2RecoveryTests(previous.ContinuousRoundTests):
    def setup_state(self):
        return V2Tests().state()


def load_tests(loader, tests, pattern):
    tests.addTests(loader.loadTestsFromModule(previous))
    tests.addTests(loader.loadTestsFromModule(play_checks))
    return tests


if __name__=='__main__':unittest.main()
