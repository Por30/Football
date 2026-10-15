"""Training-only depth perturbations; pure torch, no geometry or privileged labels."""
import copy
import math
import torch

DEFAULT_DEPTH_RANDOMIZATION = {
    'scale_range': [0.99, 1.01],
    'bias_m_range': [-0.005, 0.005],
    'sigma_m_range': [0.001, 0.005],
    'sigma_distance_range': [0., 0.001],  # sigma(z) = sigma_m + coefficient * z^2
    'hole_probability_range': [0., 0.005],
    'edge_hole_probability_range': [0., 0.02],
    'edge_threshold_m': 0.1,
}


def validate_range(values, name, minimum=None, maximum=None, positive=False):
    if (not isinstance(values, (list, tuple)) or len(values) != 2
            or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values)
            or values[0] > values[1] or (minimum is not None and values[0] < minimum)
            or (maximum is not None and values[1] > maximum) or (positive and values[0] <= 0)):
        raise ValueError('Invalid randomization range: '+name)


def validate_depth_randomization(cfg):
    if set(cfg) != set(DEFAULT_DEPTH_RANDOMIZATION):
        raise ValueError('Incomplete/unsupported v5 depth randomization keys')
    validate_range(cfg['scale_range'], 'scale_range', positive=True)
    validate_range(cfg['bias_m_range'], 'bias_m_range')
    for key in ('sigma_m_range', 'sigma_distance_range'):
        validate_range(cfg[key], key, minimum=0.)
    for key in ('hole_probability_range', 'edge_hole_probability_range'):
        validate_range(cfg[key], key, minimum=0., maximum=1.)
    threshold=cfg['edge_threshold_m']
    if not isinstance(threshold,(float,int)) or not math.isfinite(threshold) or threshold <= 0:
        raise ValueError('Invalid edge threshold')


class DepthRandomizer:
    """Per-episode sensor parameters; call apply exactly once for each captured row."""
    def __init__(self, num_envs, device, cfg, enabled=True, near=.1, far=3.):
        validate_depth_randomization(cfg)
        self.cfg, self.enabled, self.near, self.far = copy.deepcopy(cfg), enabled, near, far
        self.ids=torch.arange(num_envs, device=device)
        self.parameters={key:torch.zeros(num_envs,1,1,device=device) for key in cfg if key.endswith('_range')}
        self.reset()

    def reset(self, env_ids=None):
        ids=self.ids if env_ids is None else env_ids
        for key, value in self.parameters.items():
            lo,hi=self.cfg[key]
            if self.enabled:
                value[ids]=torch.empty_like(value[ids]).uniform_(lo,hi)
            else:
                value[ids]=1. if key=='scale_range' else 0.

    def apply(self, raw, env_ids):
        if not self.enabled:
            return raw.clone()
        p={k:v[env_ids] for k,v in self.parameters.items()}
        hit=torch.isfinite(raw)&(raw>=self.near)&(raw<self.far)
        depth=torch.nan_to_num(raw,nan=self.far,posinf=self.far,neginf=self.far).clamp(self.near,self.far)
        sigma=p['sigma_m_range']+p['sigma_distance_range']*depth.square()
        noisy=depth*p['scale_range']+p['bias_m_range']+torch.randn_like(depth)*sigma
        # Neighbour differences use no wraparound across image borders.
        edges=torch.zeros_like(hit)
        delta=(depth[:,:,1:]-depth[:,:,:-1]).abs()>self.cfg['edge_threshold_m']
        edges[:,:,1:] |= delta;edges[:,:,:-1] |= delta
        delta=(depth[:,1:,:]-depth[:,:-1,:]).abs()>self.cfg['edge_threshold_m']
        edges[:,1:,:] |= delta;edges[:,:-1,:] |= delta
        holes=(torch.rand_like(depth)<p['hole_probability_range'])
        holes |= edges & (torch.rand_like(depth)<p['edge_hole_probability_range'])
        return torch.where(hit & ~holes, noisy.clamp(self.near,self.far), self.far)
