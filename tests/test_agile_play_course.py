"""Checkpoint environment progress must load independently of optimizer state."""
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import torch
import test_soccer_v3 as fixtures
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball import AgileKickballState

class PlayCourseTests(unittest.TestCase):
    def test_inference_load_restores_course_without_optimizer_or_ball_teleport(self):
        alg,_=fixtures.make_algorithm()
        runner=BallRegressionOnPolicyRunner.__new__(BallRegressionOnPolicyRunner)
        runner.alg=alg;runner.device='cpu';runner.current_learning_iteration=12
        runner.logger_type='tensorboard';runner.disable_logs=True
        env,_=fixtures.state_fixture(); kb=AgileKickballState(env);env._kickball=kb
        kb.reset(torch.arange(2));kb.exposure_offset=145000.;kb.incoming_steps[:]=500.
        runner.env=NS(unwrapped=env)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'model.pt';runner.save(str(p))
            kb.exposure_offset=0.;kb.incoming_steps.zero_()
            before=env.scene['ball'].data.root_pos_w.clone()
            # A load with False must never touch any optimizer.
            def forbidden(*a,**kw):raise AssertionError('Optimizer loaded during inference')
            alg.optimizer.load_state_dict=forbidden
            alg.ball_aux_optimizer.load_state_dict=forbidden
            alg.amp_optimizer.load_state_dict=forbidden
            runner.load(str(p),load_optimizer=False)
            self.assertEqual(kb.exposure_steps,145500.)
            self.assertAlmostEqual(kb.serve_speed_range[1],1.5275)
            self.assertEqual(kb.serve_distance_range,(1.3,2.))
            torch.testing.assert_close(before,env.scene['ball'].data.root_pos_w)
            # Explicit play reset applies the restored course to its very first ball.
            kb.reset(torch.arange(2))
            distance=(env.scene['ball'].data.root_pos_w[:,:2]-kb.anchor_xy).norm(dim=-1)
            self.assertTrue(((distance>=1.3)&(distance<=2.)).all())

if __name__=='__main__':unittest.main()
