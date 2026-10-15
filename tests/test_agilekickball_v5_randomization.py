"""Physical units, sensor parameter lifecycle, missing returns and bounded noise."""
import copy
import unittest
import torch
import test_agilekickball_v5  # Existing lightweight package fixtures.
from perceptual_ball.kickball_randomization import DepthRandomizer, DEFAULT_DEPTH_RANDOMIZATION, validate_range


def neutral():
    cfg=copy.deepcopy(DEFAULT_DEPTH_RANDOMIZATION)
    for key in cfg:
        if key.endswith('_range'):cfg[key]=[1.,1.] if key=='scale_range' else [0.,0.]
    return cfg


class RandomizationTests(unittest.TestCase):
    def test_invalid_parameters(self):
        for values in ((-1.,1.),(1.,0.),(float('nan'),1.),(0.,1.)):
            with self.assertRaises(ValueError):validate_range(values,'kp',positive=True)
        for key,value in [('hole_probability_range',[0.,1.1]),('sigma_m_range',[-.1,0.]),('edge_threshold_m',0.)]:
            cfg=neutral();cfg[key]=value
            with self.assertRaises(ValueError):DepthRandomizer(2,'cpu',cfg)

    def test_miss_holes_edge_and_clipping(self):
        cfg=neutral();ids=torch.arange(2)
        raw=torch.ones(2,5,8);raw[:,:,:3]=3.
        randomizer=DepthRandomizer(2,'cpu',cfg)
        torch.testing.assert_close(randomizer.apply(raw,ids),raw,rtol=0,atol=0)
        cfg['bias_m_range']=[-.02,-.02]
        randomizer=DepthRandomizer(2,'cpu',cfg)
        actual=randomizer.apply(raw,ids)
        self.assertTrue((actual[:,:,:3]==3.).all())
        self.assertTrue(torch.allclose(actual[:,:,3:],torch.full_like(actual[:,:,3:],.98)))
        cfg=neutral();cfg['hole_probability_range']=[1.,1.]
        self.assertTrue((DepthRandomizer(2,'cpu',cfg).apply(raw,ids)==3.).all())
        cfg=neutral();cfg['edge_hole_probability_range']=[1.,1.]
        actual=DepthRandomizer(2,'cpu',cfg).apply(raw,ids)
        self.assertTrue((actual[:,:,3]==3.).all());self.assertTrue((actual[:,:,4:]==1.).all())
        cfg=neutral();cfg['bias_m_range']=[-1.,-1.]
        self.assertTrue((DepthRandomizer(2,'cpu',cfg).apply(raw,ids)[:,:,3:]==.1).all())

    def test_distance_noise_statistics_and_disable(self):
        torch.manual_seed(42)
        cfg=neutral();cfg['sigma_distance_range']=[.001,.001]
        raw=torch.stack([torch.ones(100,100),torch.full((100,100),2.)])
        actual=DepthRandomizer(2,'cpu',cfg).apply(raw,torch.arange(2))
        error=actual-raw
        for index,expected in enumerate((.001,.004)):
            self.assertLess(abs(error[index].mean().item()),expected*.04)
            self.assertAlmostEqual(error[index].std().item()/expected,1.,delta=.04)
        off=DepthRandomizer(2,'cpu',DEFAULT_DEPTH_RANDOMIZATION,enabled=False)
        torch.testing.assert_close(off.apply(raw,torch.arange(2)),raw,atol=0,rtol=0)

    def test_episode_ranges_and_reverse_subset_reset(self):
        randomizer=DepthRandomizer(4,'cpu',DEFAULT_DEPTH_RANDOMIZATION)
        before={k:v.clone() for k,v in randomizer.parameters.items()}
        randomizer.reset(torch.tensor([3,1]))
        for key,value in randomizer.parameters.items():
            lo,hi=DEFAULT_DEPTH_RANDOMIZATION[key]
            self.assertTrue(((value>=lo)&(value<=hi)).all())
            torch.testing.assert_close(value[[0,2]],before[key][[0,2]],atol=0,rtol=0)
            self.assertFalse(torch.equal(value[[3,1]],before[key][[3,1]]))


if __name__=='__main__':unittest.main()
