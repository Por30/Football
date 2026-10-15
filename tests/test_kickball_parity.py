"""Actual training-source replay, compiled mass/contact and USD-frame checks."""
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/sim2sim'))
import audit_kickball_parity as audit
import kickball_mujoco as s2s


class TrainingParity(unittest.TestCase):
    def test_actual_training_depth_replay(self):
        positions,quats,balls = audit.samples()
        reference = audit.training_depth(positions,quats,balls)
        candidate = np.stack([s2s.policy_depth(*s) for s in zip(positions,quats,balls)])
        np.testing.assert_array_equal(reference<3,candidate<3)
        np.testing.assert_allclose(candidate,reference,rtol=0,atol=1.e-4)
        legacy = np.stack([audit.legacy_depth(*s) for s in zip(positions,quats,balls)])
        # This dataset actually detects the old nonunit-quaternion bug.
        self.assertGreater(audit.depth_metrics(reference,legacy)['hit_mask_mismatches'],0)

    def test_compiled_ball_parameters_and_unmatched_contacts(self):
        sim = s2s.KickballSim(physics_dt=.005)
        result = audit.physical_audit(sim)
        for key in ('ball_mass_kg','ball_radius_m','policy_dt_s','physics_dt_s'):
            self.assertAlmostEqual(result[key]['training'],result[key]['mujoco'])
        np.testing.assert_allclose(result['ball_inertia_kg_m2'],np.full(3,.4*.43*.11**2))
        self.assertEqual(result['ball_damping']['mujoco_dof_damping'],[0.]*6)
        self.assertEqual(result['ball_damping']['training_linear_rate'],.02)
        self.assertAlmostEqual(result['mujoco_ball_floor_contact']['friction'][0],.6)
        # condim=3: the extra friction slots do not imply rolling resistance.
        self.assertEqual(result['mujoco_ball_floor_contact']['dim'],3)

    def test_usd_camera_frame_difference_depends_on_waist_pose(self):
        cases = audit.geometry_audit(s2s.KickballSim())
        np.testing.assert_allclose(cases[0]['camera_position_difference_m'],[0,0,.01],atol=1.e-8)
        self.assertGreater(abs(cases[1]['camera_position_difference_m'][1]),.005)
        self.assertGreater(sum(c['depth']['hit_mask_mismatches'] for c in cases),0)

    def test_observe_depth_history_is_training_frame_order(self):
        sim = s2s.KickballSim()
        frames = []
        for i in range(10):
            sim.data.qpos[sim.bq] = 2-.05*i
            audit.mujoco.mj_forward(sim.model,sim.data)
            expected = audit.training_depth(sim.data.xpos[sim.torso][None],
                sim.data.xquat[sim.torso][None],sim.data.xpos[sim.ball_body][None])[0]
            frames.append(expected)
            _,stack = sim.observe()
            history = ([frames[0]]*7+frames)[-8:]
            np.testing.assert_allclose(stack[0],np.stack(history),rtol=0,atol=1.e-4)
        self.assertEqual(stack.shape,(1,8,27,48))


if __name__ == '__main__':
    unittest.main()
