"""CUDA regression for exact box-symmetry membership under training TF32."""
import importlib.util
import json
from pathlib import Path
import unittest

import torch

source = Path(__file__).resolve().parents[1] / 'source/perceptual_ball/perceptual_ball/carrybox_wall12.py'
spec = importlib.util.spec_from_file_location('wall12_pose_math', source)
pose = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pose)


@unittest.skipUnless(torch.cuda.is_available(), 'requires CUDA TF32 hardware')
class Wall12TF32Tests(unittest.TestCase):
    def test_exact_membership_and_finite_large_batch_backward(self):
        sizes_cpu = torch.tensor([[.21,.30,.25], [.30,.30,.25], [.30,.25,.30],
                                  [.25,.30,.30], [.30,.30,.30], [.30,.30001,.25]])
        expected_counts = [4,8,8,8,24,4]
        rotations_cpu = pose.box_rotations(torch.device('cpu'), torch.float32)
        # Independent float64 arithmetic is the original mathematical definition.
        reference = torch.einsum('kij,nj->nki', rotations_cpu.double().abs(), sizes_cpu.double())
        expected = torch.isclose(reference, sizes_cpu.double()[:,None], atol=1.e-6, rtol=1.e-5).all(-1)
        self.assertEqual(expected.sum(-1).tolist(), expected_counts)
        saved = torch.backends.cuda.matmul.allow_tf32
        diagnostics = []
        try:
            for enabled in (False, True):
                torch.backends.cuda.matmul.allow_tf32 = enabled
                for n in (92, 8192):
                    sizes = sizes_cpu.repeat((n+5)//6, 1)[:n].cuda()
                    rotations = pose.box_rotations(sizes.device, sizes.dtype)
                    mask = pose.box_symmetry_mask(sizes, rotations)
                    torch.testing.assert_close(mask.cpu(), expected.repeat((n+5)//6,1)[:n], rtol=0, atol=0)
                    # Position is exact and orientation uses an identity target.
                    target = torch.cat((torch.tensor([.2,-.1,1.,1.,0.,0.,0.,1.,0.],device='cuda').expand(n,-1),sizes),-1)
                    prediction = (target[:,:9] + .01).clone().requires_grad_()
                    loss = sum(pose.box_pose_loss(prediction,target))
                    self.assertTrue(torch.isfinite(loss).item())
                    loss.backward()
                    self.assertTrue(torch.isfinite(prediction.grad).all().item())
                    self.assertGreater(torch.count_nonzero(prediction.grad).item(),0)
                    old_transformed = torch.einsum('kij,nj->nki',rotations.abs(),sizes)
                    old_mask = torch.isclose(old_transformed,sizes[:,None],atol=1.e-6,rtol=1.e-5).all(-1)
                    diagnostics.append(dict(tf32=enabled,batch=n,original_empty_rows=int((~old_mask.any(-1)).sum()),
                                            fixed_empty_rows=int((~mask.any(-1)).sum()),loss=float(loss.detach())))
            print(json.dumps(diagnostics,indent=2))
        finally:
            torch.backends.cuda.matmul.allow_tf32 = saved


if __name__ == '__main__':
    torch.set_num_threads(2)
    unittest.main(verbosity=2)
