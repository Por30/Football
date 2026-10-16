"""Scene optics, real mesh occlusion, live geometry and export boundaries."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import mujoco
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts/sim2sim'))
import kickball_mujoco as s2s
from scene_depth import SceneDepthCamera, camera_contract, select_profile

LEGACY_PROFILE = s2s.ROOT/'docs/agilekickball_v5/camera_nominal.json'


def profile():
    p = camera_contract.load_profile(LEGACY_PROFILE)
    p.update(position_m=[0., 0., 0.], quaternion_wxyz_world=[1., 0., 0., 0.])
    return p


def scene(geoms, robot='', p=None):
    model = mujoco.MjModel.from_xml_string('<mujoco><worldbody>'+geoms+
        '<body name="torso_link">'+robot+'</body></worldbody></mujoco>')
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    parent = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'torso_link')
    return model, data, SceneDepthCamera(model, p or profile(), parent)


def wall(front):
    return f'<geom name="wall" type="box" pos="{front+.02} 0 0" size=".02 10 10"/>'


class SceneOptics(unittest.TestCase):
    def test_optical_z_and_off_axis_far_plane(self):
        _, data, camera = scene(wall(2.8))
        depth = camera.sample(data)
        self.assertGreater(2.8/camera.cosine.min(), 3.)
        np.testing.assert_allclose(depth, 2.8, atol=1.e-6)
        self.assertEqual(depth.dtype, np.float32)

    def test_near_occluder_does_not_hide_valid_surface(self):
        for position, halfsize, expected in ((.05, .01, 1.2), (.1, .05, .15)):
            with self.subTest(position=position):
                _, data, camera = scene(wall(1.2)+
                    f'<geom type="box" pos="{position} 0 0" size="{halfsize} 10 10"/>')
                np.testing.assert_allclose(camera.sample(data), expected, atol=1.e-6)

    def test_far_empty_and_invisible_geometry(self):
        for geoms in ('', wall(3.2), '<geom type="box" pos="1 0 0" size=".1 10 10" rgba="1 1 1 0"/>'):
            _, data, camera = scene(geoms)
            np.testing.assert_array_equal(camera.sample(data), np.full((27, 48), 3.))

    def test_robot_visual_surface_hides_ball_and_excludes_collision_proxy(self):
        # The large collision proxy would wrongly report x=.25. The physical
        # visual box at x=.75 hides the entire sphere at either ball position.
        robot = ('<body name="arm" pos=".8 0 0">'
                 '<geom name="arm_visual" type="box" size=".05 .35 .35" contype="0" conaffinity="0"/>'
                 '<geom name="arm_collision" type="box" size=".55 .6 .6"/></body>')
        ball = '<body name="ball" pos="1.4 0 0"><freejoint/><geom name="ball_geom" type="sphere" size=".11" mass=".43"/></body>'
        model, data, camera = scene(ball, robot)
        groups, qpos, qvel = model.geom_group.copy(), data.qpos.copy(), data.qvel.copy()
        before = camera.sample(data)
        visual = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'arm_visual')
        collision = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'arm_collision')
        mask = camera.hit_geoms.reshape(27, 48) == visual
        self.assertGreater(mask.sum(), 100)
        np.testing.assert_allclose(before[mask], .75, atol=1.e-6)
        self.assertFalse(camera.visible_geoms[collision])
        np.testing.assert_array_equal(model.geom_group, groups)
        np.testing.assert_array_equal(data.qpos, qpos)
        np.testing.assert_array_equal(data.qvel, qvel)
        data.qpos[0] = 1.7
        mujoco.mj_forward(model, data)
        camera.reset()
        after = camera.sample(data)
        np.testing.assert_array_equal(after[mask], before[mask])

    def test_static_and_dynamic_environment_and_original_groups(self):
        static = '<geom name="obstacle" group="5" type="box" pos="1 .4 0" size=".1 .12 .15"/>'
        dynamic = '<body name="prop" pos=".9 -.35 0"><freejoint/><geom name="prop_geom" type="sphere" size=".12" mass="1"/></body>'
        model, data, camera = scene(wall(2.5)+static+dynamic)
        before = camera.sample(data)
        for name in ('wall', 'obstacle', 'prop_geom'):
            self.assertIn(mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name), camera.hit_geoms)
        data.qpos[1] = -.7
        data.time = .02
        mujoco.mj_forward(model, data)
        after = camera.sample(data)
        self.assertGreater(np.count_nonzero(after != before), 0)

    def test_camera_pose_and_depth_follow_torso_rotation(self):
        p = profile()
        p['position_m'] = [.05, .02, .1]
        p['quaternion_wxyz_world'] = [np.cos(.075), 0., np.sin(.075), 0.]
        robot = '<freejoint/><geom type="sphere" size=".01" mass="1" rgba="1 1 1 0"/>'
        model, data, camera = scene(wall(2.), robot, p)
        data.qpos[:3] = [.1, -.1, .2]
        data.qpos[3:7] = [np.cos(.1), 0., 0., np.sin(.1)]
        mujoco.mj_forward(model, data)
        position, rotation = camera.pose(data)
        root_rotation = s2s.quat_matrix(data.qpos[3:7])
        np.testing.assert_allclose(position, data.qpos[:3]+root_rotation@p['position_m'])
        directions = camera.rays@rotation.T
        expected = ((2.-position[0])/directions[:, 0]*camera.cosine).clip(.1, 3.)
        np.testing.assert_allclose(camera.sample(data).ravel(), expected, atol=3.e-7)


class ScenePolicyIntegration(unittest.TestCase):
    def test_scene_adaptation_preserves_environment_contact_masks(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = s2s.ET.parse(s2s.ROBOT_XML)
            s2s.ET.SubElement(tree.getroot().find('worldbody'), 'geom', name='existing_obstacle',
                             type='box', pos='1 1 .5', size='.1 .1 .5', contype='4', conaffinity='7')
            path = Path(directory)/'scene.xml'
            tree.getroot().find('compiler').set('meshdir', str(s2s.ROBOT_XML.parent/'meshes'))
            tree.write(path)
            adapted = s2s.ET.fromstring(s2s.make_scene(path, .005))
            obstacle = adapted.find('.//geom[@name="existing_obstacle"]')
            self.assertEqual(obstacle.get('contype'), '4')
            self.assertEqual(obstacle.get('conaffinity'), '7')
            model = mujoco.MjModel.from_xml_string(s2s.ET.tostring(adapted, encoding='unicode'))
            geom = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'existing_obstacle')
            self.assertEqual(model.geom_contype[geom], 4)
            self.assertEqual(model.geom_conaffinity[geom], 7)

    def test_default_scene_ground_and_actual_g1_mesh_occlusion(self):
        sim = s2s.KickballSim()
        physics = {key: getattr(sim.model, key).copy() for key in
                   ('geom_group', 'body_mass', 'body_inertia', 'geom_contype', 'geom_conaffinity', 'actuator_ctrlrange')}
        _, stack = sim.observe()
        self.assertIn(sim.floor_geom, sim.camera.hit_geoms)
        names = sim.manifest['metadata']['joint_names']
        for name, value in dict(left_shoulder_pitch_joint=-1., left_elbow_joint=.1).items():
            sim.data.qpos[sim.qadr[names.index(name)]] = value
        sim.data.time = .02
        mujoco.mj_forward(sim.model, sim.data)
        _, moved = sim.observe()
        ids = sim.camera.hit_geoms
        robot_hits = ids[(ids >= 0) & np.isin(sim.model.geom_bodyid[np.maximum(ids, 0)], list(sim.camera.robot_bodies))]
        self.assertGreater(len(robot_hits), 100)
        self.assertTrue(np.all(sim.model.geom_type[robot_hits] == mujoco.mjtGeom.mjGEOM_MESH))
        np.testing.assert_array_equal(moved[0, -2], stack[0, -1])
        self.assertGreater(np.count_nonzero(moved[0, -1] != stack[0, -1]), 100)
        for key, old in physics.items():
            np.testing.assert_array_equal(getattr(sim.model, key), old)

    def test_capture_hold_history_and_reset(self):
        p = select_profile('scene', None)
        p['update_period_s'] = .04
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'profile.json'
            path.write_text(json.dumps(p))
            sim = s2s.KickballSim(camera_profile=path)
        _, first = sim.observe()
        for time_s, x in ((.02, 1.4), (.04, 1.)):
            sim.data.time = time_s
            sim.data.qpos[sim.bq] = x
            mujoco.mj_forward(sim.model, sim.data)
            _, stack = sim.observe()
            if time_s == .02:
                np.testing.assert_array_equal(stack, first)
                self.assertEqual(sim.camera.capture_count, 1)
        self.assertEqual(sim.camera.capture_count, 2)
        self.assertEqual(sim.camera.capture_time_s, .04)
        self.assertGreater(np.count_nonzero(stack[0, -1] != first[0, -1]), 0)
        np.testing.assert_array_equal(stack[0, -2], first[0, -1])
        sim.reset()
        self.assertEqual(sim.camera.capture_count, 0)
        _, stack = sim.observe()
        for frame in stack[0]:
            np.testing.assert_array_equal(frame, stack[0, -1])

    def test_source_contract_profile_selection_and_rejection(self):
        p = profile()
        contract = camera_contract.depth_contract(p)
        self.assertEqual(select_profile('scene', contract), p)
        for key, value in dict(schema=9, backend='other', geometry='ball_only', output='range',
                               normalization='divide_by_3', history_order='newest_first',
                               feedback_gate='truth_visibility', target_intrinsics=[1., 1., 0., 0.]).items():
            with self.subTest(key=key), self.assertRaises(ValueError):
                select_profile('scene', dict(contract, **{key: value}))
        for broken in ({}, dict(contract, profile=None), dict(contract, profile=dict(p, update_period_s=1/30))):
            with self.assertRaises(ValueError):
                select_profile('scene', broken)
        with self.assertRaises(ValueError):
            select_profile('analytic', contract)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'different.json'
            path.write_text(json.dumps(dict(p, position_m=[.1, 0., 0.])))
            with self.assertRaises(ValueError):
                select_profile('scene', contract, path)
        self.assertIsNone(select_profile('analytic', None))

    def test_v5_export_loads_and_infers_with_scene_contract(self):
        # Validation-only weights plus deployment joint metadata from the same
        # G1 task. This tests loading, never claims these weights are trained.
        fixture = s2s.ROOT/'docs/agilekickball_v5/randomization/validation/export'
        manifest = json.loads((s2s.RUN/'exported/manifest.json').read_text())
        source = json.loads((fixture/'manifest.json').read_text())['metadata']['depth_contract']
        manifest['metadata']['depth_contract'] = source
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'manifest.json').write_text(json.dumps(manifest))
            shutil.copyfile(fixture/'policy.pt', path/'policy.pt')
            sim = s2s.KickballSim(export_dir=path)
            self.assertFalse(sim.depth_distribution_shift)
            self.assertEqual(sim.camera.profile, source['profile'])
            flat, depth = sim.observe()
            with torch.inference_mode():
                action = sim.policy(torch.from_numpy(flat), torch.from_numpy(depth))
            self.assertEqual(tuple(action.shape), (1, 29))
            self.assertTrue(torch.isfinite(action).all())
            with self.assertRaises(ValueError):
                s2s.KickballSim(export_dir=path, depth_mode='analytic')

    def test_hardware_preprocessing_and_bad_profiles(self):
        p = camera_contract.load_profile(LEGACY_PROFILE)
        raw = torch.full((1, 27, 48), 1250.)
        raw[0, 0, :3] = torch.tensor([0., float('nan'), -1.])
        clean = camera_contract.preprocess_hardware_depth(raw, p)
        torch.testing.assert_close(clean[0, 0, :3], torch.full((3,), 3.))
        self.assertEqual(float(clean[0, 1, 1]), 1.25)
        for change in ({'quaternion_wxyz_world': [1., 1., 0., 0.]}, {'rectified': False},
                       {'calibration_status': 'calibrated'}, {'update_period_s': 1/30}):
            with self.assertRaises(ValueError):
                camera_contract.validate_profile(dict(p, **change))

    def test_official_stream_profile_and_full_frame_preprocessing(self):
        p = select_profile('scene', None)
        self.assertEqual((p['source_width'], p['source_height'], p['source_fps'], p['source_format']),
                         (640, 480, 60, 'Z16'))
        self.assertEqual(p['update_period_s'], 1/60)
        with self.assertRaises(ValueError):
            camera_contract.validate_profile(p)  # lazy 50 Hz training cannot capture 60 Hz
        raw = torch.full((1, 480, 640), 1250.)
        raw[:, :, :20] = 0
        out = camera_contract.preprocess_hardware_depth(raw, p)
        self.assertEqual(tuple(out.shape), (1, 27, 48))
        torch.testing.assert_close(out[:, :, 0], torch.full((1, 27), 3.))
        torch.testing.assert_close(out[:, :, 2:], torch.full((1, 27, 46), 1.25))
        with self.assertRaisesRegex(ValueError, 'physics_dt exceeds'):
            s2s.KickballSim(physics_dt=.02)

    def test_sixty_hz_physics_capture_and_fifty_hz_policy_consumption(self):
        sim = s2s.KickballSim(physics_dt=.005)
        sim.observe()
        for tick in range(1, 21):
            if tick == 7:  # change geometry at a non-policy capture tick
                sim.data.qpos[sim.bq+1] = -.3
            sim.data.ctrl[:] = 0
            mujoco.mj_step(sim.model, sim.data)
            sim.capture_depth_at_physics_tick()
            if tick == 7:
                actual = sim.camera.latest.copy()
                mujoco.mj_forward(sim.model, sim.data)
                reference = SceneDepthCamera(sim.model, sim.camera.profile, sim.pelvis).sample(sim.data)
                np.testing.assert_allclose(actual, reference, rtol=0, atol=1.e-6)
            if tick % 4 == 0:
                sim.observe()
        events = sim.camera.capture_events
        np.testing.assert_allclose([e['scheduled_time_s'] for e in events], np.arange(7)/60, atol=1.e-12)
        np.testing.assert_allclose([e['actual_time_s'] for e in events], [0, .02, .035, .05, .07, .085, .1], atol=1.e-12)
        self.assertEqual(len(sim.camera.policy_samples), 6)
        self.assertEqual(sum(e['consumed'] for e in events), 6)
        self.assertEqual(sum(e['overwritten_before_consumption'] for e in events), 1)
        self.assertEqual(sum(e['missed_scheduled_frames'] for e in events), 0)
        self.assertLessEqual(max(e['quantization_delay_s'] for e in events), .005+1.e-9)
        self.assertTrue(all(0 <= p['frame_age_s'] < 1/60+.005 for p in sim.camera.policy_samples))
        sim.serve()
        self.assertEqual(sim.camera.capture_count, 7)
        self.assertEqual(sim.camera.next_capture_index, 7)

    def test_clock_jump_records_missed_frames_without_fabricating_samples(self):
        p = select_profile('scene', None)
        p.update(position_m=[0., 0., 0.], quaternion_wxyz_world=[1., 0., 0., 0.])
        _, data, camera = scene(wall(1.2), p=p)
        camera.consume(data)
        data.time = .1
        camera.consume(data)
        self.assertEqual(camera.capture_count, 2)
        self.assertEqual(camera.capture_events[-1]['missed_scheduled_frames'], 5)
        self.assertAlmostEqual(camera.capture_events[-1]['scheduled_time_s'], .1)
        camera.consume(data)
        self.assertEqual(camera.capture_count, 2)
        self.assertEqual(camera.policy_samples[-1]['frame_age_s'], 0)


if __name__ == '__main__':
    unittest.main()
