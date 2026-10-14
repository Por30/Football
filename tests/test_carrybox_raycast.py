"""Exercise the actual Warp kernel on CPU, including clipping and moving meshes."""
import importlib.util
from pathlib import Path
import unittest
import ast
import json
import os
import tempfile
from types import SimpleNamespace
import numpy as np
import warp as wp

path = Path(__file__).resolve().parents[1] / 'source/perceptual_ball/perceptual_ball/carrybox_raycast.py'
spec = importlib.util.spec_from_file_location('carrybox_raycast_tested', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RaycastTests(unittest.TestCase):
    def test_cli_warm_start_creates_new_run_directory(self):
        # Execute the real CLI branch without importing AppLauncher/starting GPU.
        source = (path.parents[3] / 'scripts/rsl_rl/train.py').read_text()
        tree = ast.parse(source)
        branches = [node for node in ast.walk(tree) if isinstance(node, ast.If)
                    and isinstance(node.test, ast.Attribute)
                    and node.test.attr == 'warm_start_carrybox']
        self.assertEqual(len(branches), 1)
        class Runner:
            def warm_start(self, checkpoint):
                self.warm_start_info = {'source': checkpoint}
        with tempfile.TemporaryDirectory() as directory:
            log_dir = os.path.join(directory, 'new_run')
            scope = dict(os=os, args_cli=SimpleNamespace(warm_start_carrybox='official.pt'),
                         runner=Runner(), CarryBoxOnPolicyRunner=Runner, log_dir=log_dir)
            exec(compile(ast.Module(body=branches, type_ignores=[]), '<actual-train-branch>', 'exec'), scope)
            self.assertEqual(json.loads(Path(log_dir, 'initialization.json').read_text()), {'source':'official.pt'})

    def test_optical_clipping_nearest_dynamic_and_subset(self):
        wp.init()
        mesh = wp.Mesh(points=wp.array([[0., -10., -10.], [0., 10., -10.], [0., 10., 10.], [0., -10., 10.]],
                                      dtype=wp.vec3, device='cpu'),
                       indices=wp.array([0, 1, 2, 0, 2, 3], dtype=wp.int32, device='cpu'))
        directions = np.array([[1., 0., 0.], [1., .8, .3]], dtype=np.float32)
        directions /= np.linalg.norm(directions, axis=1, keepdims=True)
        camera = np.zeros((2, 7), dtype=np.float32); camera[:, 6] = 1.
        poses = np.zeros((2, 3, 7), dtype=np.float32); poses[:, :, 6] = 1.
        poses[:, :, 0] = [.05, 2., 2.5]  # First surface before near, second nearest valid.
        def run():
            depth = wp.array(np.full((2, 2), -1., dtype=np.float32), device='cpu')
            wp.launch(module.optical_depth, dim=(1, 2), inputs=[
                wp.array([1], dtype=wp.int32, device='cpu'), wp.array(camera, dtype=wp.transform, device='cpu'),
                wp.array(directions, dtype=wp.vec3, device='cpu'),
                wp.array([mesh.id]*3, dtype=wp.uint64, device='cpu'),
                wp.array(poses, dtype=wp.transform, device='cpu'), .1, 3., depth], device='cpu')
            result = depth.numpy()
            np.testing.assert_array_equal(result[0], [-1., -1.])
            return result[1]
        np.testing.assert_allclose(run(), [2., 2.], atol=1e-5)
        poses[1, 2, 0] = 1.2  # A moving blocker becomes the nearest surface.
        np.testing.assert_allclose(run(), [1.2, 1.2], atol=1e-5)
        poses[1, :, 0] = [.05, 3.5, 4.]
        np.testing.assert_allclose(run(), [3., 3.], atol=1e-5)


if __name__ == '__main__':
    unittest.main()
