"""Ball-only edits and actual Tk controls through the graphical s2s loop."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import mujoco
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/sim2sim'))
import kickball_mujoco as s2s
from depth_visualization import LiveDepthWindow


class BallSpeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = s2s.KickballSim()

    def setUp(self):
        self.sim.speed = 2.
        self.sim.reset()

    def test_next_serve_and_invalid_values(self):
        sim = self.sim
        qpos, qvel = sim.data.qpos.copy(), sim.data.qvel.copy()
        sim.apply_ball_command('set',3.5)
        np.testing.assert_array_equal(sim.data.qpos,qpos)
        np.testing.assert_array_equal(sim.data.qvel,qvel)
        for invalid in (0.,-1.,np.nan,np.inf):
            with self.assertRaises(ValueError):
                sim.apply_ball_command('apply',invalid)
            self.assertEqual(sim.speed,3.5)
            np.testing.assert_array_equal(sim.data.qvel,qvel)
        sim.serve()
        np.testing.assert_allclose(sim.data.qvel[sim.bv:sim.bv+3],[-3.5,0,0])

    def test_apply_preserves_direction_robot_and_position(self):
        sim = self.sim
        d = sim.data
        d.qpos[sim.bq+3:sim.bq+7] = [np.cos(.6),np.sin(.6),0,0]
        d.qvel[sim.bv:sim.bv+6] = [3,4,.7,0,0,0]
        qpos, robot_qvel = d.qpos.copy(), d.qvel[:sim.bv].copy()
        history, action = sim.history, sim.last_action.copy()
        sim.apply_ball_command('apply',2.5)
        np.testing.assert_array_equal(d.qpos,qpos)
        np.testing.assert_array_equal(d.qvel[:sim.bv],robot_qvel)
        np.testing.assert_allclose(d.qvel[sim.bv:sim.bv+3],[1.5,2,.7])
        world_velocity = np.zeros(6)
        mujoco.mj_objectVelocity(sim.model,d,mujoco.mjtObj.mjOBJ_BODY,sim.ball_body,world_velocity,0)
        np.testing.assert_allclose(world_velocity[:3],[-2/.11,1.5/.11,0],atol=1e-12)
        self.assertIs(sim.history,history)
        np.testing.assert_array_equal(sim.last_action,action)

    def test_stationary_ball_and_manual_serve(self):
        sim = self.sim
        sim.data.qvel[sim.bv:sim.bv+6] = 0
        sim.apply_ball_command('apply',1.5)
        np.testing.assert_allclose(sim.data.qvel[sim.bv:sim.bv+3],[-1.5,0,0])
        sim.data.qpos[sim.bq] = -1
        sim.ball_active = False
        sim.wait_elapsed = 2.
        qpos, qvel = sim.data.qpos[:sim.bq].copy(),sim.data.qvel[:sim.bv].copy()
        history = sim.history
        sim.apply_ball_command('serve',3.)
        np.testing.assert_array_equal(sim.data.qpos[:sim.bq],qpos)
        np.testing.assert_array_equal(sim.data.qvel[:sim.bv],qvel)
        np.testing.assert_allclose(sim.data.qpos[sim.bq:sim.bq+3],[2,.15,.11])
        self.assertTrue(sim.ball_active)
        self.assertEqual(sim.wait_elapsed,0)
        self.assertIs(sim.history,history)

    def test_real_gui_controls_in_s2s(self):
        windows = []

        def window_factory(speed):
            window = LiveDepthWindow(speed)
            windows.append(window)

            def apply():
                window.speed_slider.set(3.)
                window.apply_button.invoke()

            def serve():
                window.speed_slider.set(1.5)
                window.serve_button.invoke()

            window.root.after(200,apply)
            window.root.after(600,serve)
            # Closing only the control/depth window must leave the run alive.
            window.root.after(1200,window.close)
            return window

        output = s2s.ROOT/'docs/agilekickball_v4/sim2sim_20261014/ball_speed_20261015/gui_smoke.json'
        args = SimpleNamespace(export_dir=s2s.RUN/'exported',robot_xml=s2s.ROBOT_XML,
            physics_dt=.005,speed=2.,duration=2.,headless=False,no_depth_window=False,
            serve_mode='recovery',depth_output=None,output=output)
        with patch('depth_visualization.LiveDepthWindow',side_effect=window_factory):
            self.assertEqual(s2s.run(args),0)
        result = json.loads(output.read_text())
        events = result['ball_speed_commands']
        self.assertTrue(any(e['action']=='apply' and e['speed_m_s']==3 for e in events))
        self.assertTrue(any(e['action']=='serve' and e['speed_m_s']==1.5 for e in events))
        self.assertEqual(result['manual_serves'],1)
        self.assertEqual(result['steps'],100)
        self.assertEqual(result['errors'],[])
        self.assertGreater(result['depth_window_frames'],0)
        self.assertTrue(windows[0].closed)


if __name__ == '__main__':
    unittest.main()
