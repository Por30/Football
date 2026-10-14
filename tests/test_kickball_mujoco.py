"""Numerical contract checks independent of IsaacSim and GPU training."""
import importlib.util
from pathlib import Path
import unittest

import mujoco
import numpy as np
import torch

SPEC = importlib.util.spec_from_file_location('kickball_s2s', Path(__file__).resolve().parents[1]/'scripts/sim2sim/kickball_mujoco.py')
s2s = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s2s)


class ObservationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = s2s.KickballSim()

    def setUp(self):
        self.sim.reset()

    def test_history_term_order_reset_and_roll(self):
        hist = s2s.History()
        terms = [np.arange(n)+100*k for k,n in enumerate(s2s.TERM_DIMS)]
        flat, depth = hist.append(terms,np.full((27,48),2,np.float32))
        self.assertEqual(flat.shape,(1,864))
        np.testing.assert_equal(flat[0,:24],np.tile([0,1,2],8))
        np.testing.assert_equal(flat[0,24:48],np.tile([100,101,102],8))
        self.assertTrue((depth == 2).all())
        flat, depth = hist.append([v+10 for v in terms],np.ones((27,48),np.float32))
        np.testing.assert_equal(flat[0,:24],np.r_[np.tile([0,1,2],7),[10,11,12]])
        self.assertTrue((depth[0,:7] == 2).all())
        self.assertTrue((depth[0,-1] == 1).all())

    def test_name_mapping_roundtrip(self):
        sim = self.sim
        names = sim.manifest['metadata']['joint_names']
        self.assertEqual(len(set(sim.actuators)),29)
        for i,name in enumerate(names):
            self.assertEqual(mujoco.mj_id2name(sim.model,mujoco.mjtObj.mjOBJ_JOINT,int(sim.joints[i])),name)
            self.assertEqual(sim.model.actuator_trnid[sim.actuators[i],0],sim.joints[i])
        # Manifest is interleaved left/right; model is grouped by kinematic chain.
        self.assertNotEqual(sim.qadr.tolist(), sorted(sim.qadr.tolist()))
        values = np.linspace(-.02,.02,29)
        sim.data.qpos[sim.qadr] = sim.default+values
        mujoco.mj_forward(sim.model,sim.data)
        flat,_ = sim.observe()
        np.testing.assert_allclose(flat[0,48:48+29],values,atol=1e-7)

    def test_root_rotation_and_link_frame(self):
        sim = self.sim
        base,_ = sim.observe()
        old_end = base[0,512:632].reshape(8,15)[0]
        sim.data.qpos[:3] = [1,2,3]
        sim.data.qpos[3:7] = [np.sqrt(.5),np.sqrt(.5),0,0]  # +90deg roll
        sim.data.qvel[3:6] = [.1,.2,.3]  # MuJoCo free-joint angular velocity is link-local
        mujoco.mj_forward(sim.model,sim.data)
        sim.history = s2s.History()
        flat,_ = sim.observe()
        np.testing.assert_allclose(flat[0,:3],[.1,.2,.3],atol=1e-7)
        np.testing.assert_allclose(flat[0,24:27],[0,-1,0],atol=1e-6)
        np.testing.assert_allclose(flat[0,512:527],old_end,atol=1e-6)
        torso_rot = sim.data.xmat[sim.torso].reshape(3,3)
        head = sim.data.xpos[sim.torso]+torso_rot@np.array([.0039635,0,-.044])
        np.testing.assert_allclose(sim.data.site_xpos[sim.head_site],head,atol=1e-9)

    def test_action_and_torque_boundaries(self):
        sim = self.sim
        raw = np.linspace(-2,2,29,dtype=np.float32)
        target = sim.target(raw)
        np.testing.assert_allclose(target,sim.offset+.25*raw)
        np.testing.assert_array_equal(sim.last_action,raw)
        for sign,column in [(1,1),(-1,0)]:
            torque,saturated = sim.torque(np.full(29,sign*100.))
            np.testing.assert_equal(torque,sim.limits[:,column])
            self.assertEqual(saturated,29)
        index = sim.manifest['metadata']['joint_names'].index('left_wrist_pitch_joint')
        np.testing.assert_equal(sim.limits[index],[-5,5])
        with self.assertRaises(ValueError): sim.target(np.full(29,np.nan))
        with self.assertRaises(ValueError): sim.target(np.zeros(28))

    def test_ray_depth_numeric(self):
        ray = np.array([[[0,0,1]]],np.float32)
        self.assertAlmostEqual(float(s2s.ball_depth([0,0,1],ray)[0,0]),.89,places=5)
        for point in ([1,0,1],[0,0,-1],[0,0,.15],[0,0,4]):
            self.assertEqual(float(s2s.ball_depth(point,ray)[0,0]),3.)
        # Legacy v4 has half-pixel vertical centre, not v5's principal point.
        self.assertNotEqual(float(s2s.RAYS[13,24,1]),0.)

    def test_nonfinite_observation_and_timing(self):
        terms = [np.zeros(n) for n in s2s.TERM_DIMS]
        with self.assertRaises(ValueError):
            s2s.History().append(terms,np.full((27,48),np.inf))
        with self.assertRaises(ValueError):
            s2s.KickballSim(physics_dt=.003)

    def test_recovery_gate_blocks_premature_serve(self):
        sim = self.sim
        # Ball passing behind anchor ends a round. Upright robot with high speed
        # must not be marked recovered even after cooldown.
        sim.data.qpos[sim.bq] = -.5
        mujoco.mj_forward(sim.model,sim.data)
        self.assertIsNone(sim.advance_round())
        self.assertFalse(sim.ball_active)
        sim.data.qvel[0] = 1.
        for _ in range(30): self.assertIsNone(sim.advance_round())
        self.assertEqual(sim.stable_elapsed,0.)
        sim.data.qvel[0] = 0.
        mujoco.mj_forward(sim.model,sim.data)
        self.assertTrue(sim.balanced())
        for _ in range(14): self.assertIsNone(sim.advance_round())
        self.assertEqual(sim.advance_round(),'recovered_serve')
        self.assertTrue(sim.ball_active)

    def test_export_matches_final_checkpoint(self):
        ckpt = torch.load(s2s.RUN/'model_49999.pt',map_location='cpu',weights_only=False)
        self.assertEqual(ckpt['iter'],49999)
        for key,value in self.sim.policy.state_dict().items():
            original = 'perception_encoder.'+key[len('encoder.'):] if key.startswith('encoder.') else key
            self.assertTrue(torch.equal(value,ckpt['model_state_dict'][original]),original)
        flat,depth = self.sim.observe()
        with torch.inference_mode():
            out = self.sim.policy(torch.from_numpy(flat),torch.from_numpy(depth))
        self.assertEqual(tuple(out.shape),(1,29))
        self.assertTrue(torch.isfinite(out).all())


if __name__ == '__main__':
    unittest.main()
