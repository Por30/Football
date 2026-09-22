"""Real CLI parsing and persistent overrides of real v0/v1 serve samplers."""
import argparse
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
import torch
import test_soccer_v3 as fixtures
from test_agilekickball_v1 import V1Tests
from test_agile_play_course import PlayCourseTests
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball import AgileKickballState, exposure_speed_curriculum

spec=importlib.util.spec_from_file_location('play_cli_args',Path(__file__).resolve().parents[1]/'scripts/rsl_rl/cli_args.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)

class BallSpeedTests(unittest.TestCase):
    def parser(self):
        parser=argparse.ArgumentParser();cli.add_ball_speed_arg(parser);return parser

    def test_default_range_and_fixed_speed(self):
        p=self.parser()
        self.assertIsNone(p.parse_args([]).ballspeed)
        self.assertEqual(p.parse_args(['--ballspeed','.4','5']).ballspeed,(.4,5.))
        self.assertEqual(p.parse_args(['--ballspeed','2','2']).ballspeed,(2.,2.))

    def test_invalid_speeds_are_cli_errors(self):
        for values in (['0','1'],['-1','2'],['3','2'],['nan','2'],['1','inf'],['1'],['1','2','3']):
            with self.subTest(values=values),contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as error:
                self.parser().parse_args(['--ballspeed']+values)
            self.assertEqual(error.exception.code,2)

    def test_v0_curriculum_reset_cannot_replace_explicit_speed(self):
        env,_=fixtures.state_fixture();kb=AgileKickballState(env);env._kickball=kb
        kb.serve_speed_override=(2.,2.)
        for _ in range(3):
            exposure_speed_curriculum(env,None)  # sets the ordinary course range back to .4-.8
            kb.reset(torch.arange(2))
            torch.testing.assert_close(env.scene['ball'].data.root_lin_vel_w[:,:2].norm(dim=-1),torch.full((2,),2.))
        self.assertEqual(kb.serve_speed_range,(2.,2.))

    def test_v1_override_survives_course_sync_and_recovery(self):
        env,kb=V1Tests().state(n=128)
        kb.exposure_offset=480000.;kb._sync_course();kb.curriculum_training=False
        kb.serve_speed_override=(1.,1.5)
        before=kb.curriculum_state_dict()
        for _ in range(3):
            kb._sync_course();kb.reset(torch.arange(128))
            speed=env.scene['ball'].data.root_lin_vel_w[:,:2].norm(dim=-1)
            self.assertTrue(((speed>=1.-1.e-5)&(speed<=1.5+1.e-5)).all())
            self.assertEqual(kb.serve_speed_range,(1.,1.5))
        # Ball-only recovery serve must obey the override too, without resetting the robot.
        kb.ball_active[:]=False;kb.stable_elapsed[:]=1.;kb.wait_elapsed[:]=1.
        kb._serve(torch.arange(128))
        speed=env.scene['ball'].data.root_lin_vel_w[:,:2].norm(dim=-1)
        self.assertTrue(((speed>=1.-1.e-5)&(speed<=1.5+1.e-5)).all())
        self.assertEqual(before,kb.curriculum_state_dict())
        self.assertNotIn('override',kb.curriculum_state_dict())

if __name__=='__main__':unittest.main()
