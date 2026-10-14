"""Camera units/K, feedback semantics and inherited v4 numerical regressions."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
import torch
import test_agilekickball_v4 as v4
import test_state_feedback as feedback
from perceptual_ball.kickball_depth import load_profile, target_intrinsics, preprocess_hardware_depth, depth_contract
from perceptual_ball.rsl_rl_extensions.ball_metrics import ball_prediction_metrics
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner

PROFILE = Path(__file__).resolve().parents[1]/'docs/agilekickball_v5/camera_nominal.json'


class V5Tests(unittest.TestCase):
    def test_hardware_units_invalid_and_resize(self):
        p = load_profile(PROFILE)
        raw = torch.full((1, 27, 48), 1250.)
        raw[0, 0, :6] = torch.tensor([0., float('nan'), float('inf'), -1., 50., 4000.])
        out = preprocess_hardware_depth(raw, p)
        torch.testing.assert_close(out[0,0,:6], torch.tensor([3.,3.,3.,3.,.1,3.]))
        self.assertEqual(out[0,2,2], 1.25)
        p.update(source_width=96, source_height=54, source_intrinsics=[40.,60.,47.5,26.5], crop_xywh=[0,0,96,54])
        self.assertEqual(target_intrinsics(p), (20.,30.,23.5,13.))
        raw = torch.arange(54*96).reshape(1,54,96).float()/10000
        p['depth_unit_m']=1.
        out=preprocess_hardware_depth(raw,p)
        torch.testing.assert_close(out, raw[:,1::2,1::2].clamp(.1,3.))
        with self.assertRaises(ValueError): preprocess_hardware_depth(raw[:,:27],p)

    def test_profile_rejects_unverified_conventions(self):
        p=load_profile(PROFILE)
        for changes in ({'rectified':False}, {'quaternion_wxyz_world':[1.,1.,0.,0.]},
                        {'calibration_status':'calibrated'}, {'crop_xywh':[0,0,99,27]}, {'depth_unit_m':0.}):
            with tempfile.TemporaryDirectory() as d:
                path=Path(d)/'p.json';path.write_text(json.dumps(dict(p,**changes)))
                with self.assertRaises(ValueError):load_profile(path)
        contract=depth_contract(p)
        self.assertEqual(contract['normalization'],'none')
        self.assertEqual(contract['profile']['history_length'],8)

    def test_v5_metric_and_old_warmstart_guards(self):
        alg,obs=feedback.algorithm(stable=True)
        alg.policy.feedback_scene_depth=True
        obs['perception'][:]=1.5  # Scene ground; never a ball-visibility label.
        metrics=ball_prediction_metrics(alg.policy,obs)
        self.assertIn('valid_depth/count',metrics)
        self.assertNotIn('visible/count',metrics)
        runner=BallRegressionOnPolicyRunner.__new__(BallRegressionOnPolicyRunner)
        runner.env=SimpleNamespace(unwrapped=SimpleNamespace(_kickball=SimpleNamespace(
            curriculum_checkpoint_key='agile_v5_scene_depth_curriculum')))
        runner.alg=alg;runner.current_learning_iteration=0
        for method in (runner.warm_start_from_v2,runner.warm_start_from_v3):
            with self.assertRaises(ValueError):method('/does/not/exist.pt')


def load_tests(loader, tests, pattern):
    tests.addTests(loader.loadTestsFromModule(v4))
    tests.addTests(loader.loadTestsFromModule(feedback))
    return tests

if __name__=='__main__':unittest.main()
