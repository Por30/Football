"""Noise/reset and obstacle feasibility boundaries without simulator startup."""
import unittest
import torch
import test_carrybox as fixtures
from perceptual_ball.carrybox_wall11 import DEPTH_NOISE, NoisyDepthFrame, obstacle_layout


class Wall11Tests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)

    def test_noise_units_misses_range_and_cache(self):
        depth = torch.full((8, 27, 48), 1.)
        depth[:, 0, :5] = torch.tensor([float('nan'), float('inf'), -1., 0., 3.])
        cache = NoisyDepthFrame(depth)
        first = cache.update(0, depth, DEPTH_NOISE).clone()
        self.assertTrue(torch.isfinite(first).all())
        self.assertTrue(((first >= .1) & (first <= 3.)).all())
        self.assertTrue((first[:, 0, :5] == 3.).all())
        valid = first[:, 2:] < 3
        error = (first[:, 2:] - 1)[valid]
        self.assertLess(abs(float(error.mean())), .002)
        self.assertTrue(.023 < float(error.std()) < .028)
        self.assertTrue(.01 < float((first[:, 2:] == 3).float().mean()) < .03)
        rng = torch.get_rng_state().clone()
        torch.testing.assert_close(cache.update(0, depth * .5, DEPTH_NOISE), first, atol=0, rtol=0)
        self.assertTrue(torch.equal(rng, torch.get_rng_state()))
        self.assertFalse(torch.equal(cache.update(1, depth, DEPTH_NOISE), first))

    def test_partial_reset_same_step_preserves_other_rows(self):
        depth = torch.ones(5, 27, 48)
        cache = NoisyDepthFrame(depth)
        old = cache.update(8, depth, DEPTH_NOISE).clone()
        cache.reset(torch.tensor([4, 0]))
        depth[[4, 0]] = 2.
        new = cache.update(8, depth, DEPTH_NOISE)
        torch.testing.assert_close(new[1:4], old[1:4], atol=0, rtol=0)
        self.assertGreater(float(new[[4, 0]].mean()), 1.9)
        self.assertTrue((cache.last_step == 8).all())

    def test_edge_dropouts_do_not_wrap_image_borders(self):
        depth = torch.ones(1, 8, 12)
        depth[:, :, 6:] = 2.
        noise = dict(gaussian_std=0., stereo_near=0., stereo_far=0.,
                     edge_probability=1., hole_probability=0., edge_threshold=.15)
        output = NoisyDepthFrame(depth).update(0, depth, noise)
        self.assertTrue((output[:, :, 5:7] == 3.).all())
        torch.testing.assert_close(output[:, :, 0], depth[:, :, 0])
        torch.testing.assert_close(output[:, :, -1], depth[:, :, -1])

    def test_layout_clearance_and_translation_for_large_reset_envelopes(self):
        n = 4096
        robot = torch.randn(n, 2) * 10
        bodies = robot[:, None] + torch.rand(n, 30, 2) * 1.4 - .7
        box = robot + torch.rand(n, 2) * 3 - 1.5
        sizes = torch.rand(n, 3) * .2 + .2
        rng = torch.get_rng_state()
        columns, wall, yaw, radius = obstacle_layout(robot, bodies, box, sizes)
        centre = (robot + box) / 2
        ring = (columns - centre[:, None]).norm(dim=-1)
        self.assertTrue((ring - .15 - radius[:, None] >= .19999).all())
        distances = torch.cdist(columns, columns) + torch.eye(3)[None] * 100
        self.assertTrue((distances > .3).all())
        normal = torch.stack((yaw.cos(), yaw.sin()), -1)
        column_wall_distance = ((wall[:, None] - columns) * normal[:, None]).sum(-1) - .1 - .15
        self.assertTrue((column_wall_distance >= .19999).all())
        self.assertTrue(((bodies - centre[:, None]).norm(dim=-1) + .5 <= radius[:, None] + 1.e-5).all())
        shift = torch.tensor([12., -7.])
        torch.set_rng_state(rng)
        shifted = obstacle_layout(robot + shift, bodies + shift, box + shift, sizes)
        torch.testing.assert_close(shifted[0], columns + shift, atol=1.e-5, rtol=1.e-5)
        torch.testing.assert_close(shifted[1], wall + shift, atol=1.e-5, rtol=1.e-5)


if __name__ == '__main__':
    unittest.main()
