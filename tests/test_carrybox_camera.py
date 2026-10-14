"""Partial-write and Fabric index contract independent of the simulator."""
import importlib.util
from pathlib import Path
import types
import unittest
from unittest.mock import patch
import torch


class CameraReaderTests(unittest.TestCase):
    def test_full_fabric_query_and_reversed_subset_only_write_selected_rows(self):
        sensors = types.ModuleType('isaaclab.sensors')
        class CameraBase:
            def set_world_poses(self, *args, **kwargs):
                pass
            def set_world_poses_from_view(self, *args, **kwargs):
                pass
        sensors.TiledCamera = CameraBase
        maths = types.ModuleType('isaaclab.utils.math')
        calls = []
        def convert(q, origin, target):
            calls.append((origin, target))
            return q
        maths.convert_camera_frame_orientation_convention = convert
        maths.quat_apply = lambda q, p: p  # identity parent quaternions in this fixture
        maths.quat_mul = lambda q, r: r
        path = Path(__file__).resolve().parents[1] / 'source/perceptual_ball/perceptual_ball/carrybox_camera.py'
        spec = importlib.util.spec_from_file_location('camera_reader_under_test', path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules', {'isaaclab.sensors': sensors, 'isaaclab.utils.math': maths}):
            spec.loader.exec_module(module)
        positions = torch.arange(12, dtype=torch.float).reshape(4, 3)
        quats = torch.tensor([[1., 0., 0., 0.]]).repeat(4, 1)
        queries = []
        def get_world_poses(**kwargs):
            queries.append(kwargs)
            return positions, quats
        camera = module.FabricTiledCamera()
        camera._sensor_prims = [object()] * 4
        camera._parent_view = types.SimpleNamespace(get_world_poses=get_world_poses, _view_in_fabric_prepared=True, _selection=object())
        local_reads = []
        local_p = torch.zeros(4, 3)
        def local_poses():
            local_reads.append(True)
            return local_p, quats
        def set_local(p, q, indices):
            local_p[indices] = p
        camera._view = types.SimpleNamespace(get_local_poses=local_poses, set_local_poses=set_local)
        camera._data = types.SimpleNamespace(pos_w=torch.full((4, 3), -1.), quat_w_world=torch.zeros(4, 4))
        camera._update_poses(torch.tensor([3, 1], dtype=torch.int64))
        self.assertEqual(queries, [{'usd': False}])
        self.assertIsNone(camera._parent_view._selection)
        self.assertEqual(calls, [('opengl', 'world')])
        torch.testing.assert_close(camera._data.pos_w[[3, 1]], positions[[3, 1]])
        self.assertTrue((camera._data.pos_w[[0, 2]] == -1).all())
        self.assertTrue((camera._data.quat_w_world[[0, 2]] == 0).all())
        camera._update_poses(torch.tensor([0, 2]))
        self.assertEqual(len(local_reads), 1)
        camera.set_mount_poses(torch.ones(2, 3), quats[[3, 1]], torch.tensor([3, 1]))
        camera._update_poses(torch.arange(4))
        torch.testing.assert_close(camera._data.pos_w, positions + local_p)
        self.assertEqual(len(local_reads), 1)
        for setter in [camera.set_world_poses, camera.set_world_poses_from_view]:
            setter()
            self.assertIsNone(camera._mount_cache)
            camera._update_poses(torch.arange(4))
        self.assertEqual(len(local_reads), 3)
        camera._sensor_prims = []
        with self.assertRaises(RuntimeError):
            camera._update_poses(torch.tensor([1]))


if __name__ == '__main__':
    unittest.main()
