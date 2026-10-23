"""Wall5 PhysHSI G1 reset/control contracts. No simulation dependency."""
import math
import torch

COLLISION_PROFILE = 'g1_original_urdf_shoulders_capsules_v24'
RESET_PROFILE = 'physhsi_physical_reset_fixed_four_way_quota_v27'
HYBRID_REFERENCE_PROBABILITY = .8
RSI_SKILL_PROBABILITIES = (2/3, 1/6, 1/6)


def hybrid_probabilities(reference_probability, skill_probabilities):
    """Four initialization sources; the three skill probabilities are conditional."""
    if (not math.isfinite(reference_probability) or not 0 <= reference_probability <= 1
            or len(skill_probabilities) != 3
            or any(not math.isfinite(p) or p < 0 for p in skill_probabilities)
            or abs(sum(skill_probabilities)-1.) > 1.e-6):
        raise ValueError('Invalid hybrid reset probabilities')
    return (1-reference_probability, *(reference_probability*p for p in skill_probabilities))


def fixed_hybrid(env_ids, num_envs, reference_probability, skill_probabilities):
    """Reserve transition quotas despite different episode lengths.

    Only the initialization source is fixed. Reference frame, noise and box
    placement are resampled, and the robot can progress through every task phase.
    """
    probabilities = hybrid_probabilities(reference_probability, skill_probabilities)
    if num_envs < 1:
        raise ValueError('Invalid environment count')
    edges = env_ids.new_tensor(probabilities, dtype=torch.float64).cumsum(0)[:-1]
    source = torch.bucketize((env_ids.double()+.5)/num_envs, edges, right=True)
    return (source-1).clamp_min(0), source == 0


def sample_hybrid(count, device='cpu'):
    reference = torch.rand(count, device=device) < HYBRID_REFERENCE_PROBABILITY
    skills = torch.multinomial(torch.tensor(RSI_SKILL_PROBABILITIES, device=device), count, replacement=True)
    # Default starts are empty-handed and use the existing loco metric group.
    return torch.where(reference, skills, 0), ~reference


def interpolate(value, times, quaternion=False):
    lo = times.floor().long()
    hi = (lo+1).clamp_max(len(value)-1)
    w = (times-lo).reshape(-1, *([1]*(value.ndim-1)))
    a, b = value[lo], value[hi]
    if quaternion:
        b = torch.where((a*b).sum(-1, keepdim=True) < 0, -b, b)
    result = a*(1-w)+b*w
    return torch.nn.functional.normalize(result, dim=-1) if quaternion else result


class PhysicalActionDelay:
    """Five physics-step slots, newest index4. Reset pre-fills physical targets."""
    def __init__(self, target):
        self.buffer = target.unsqueeze(0).repeat(5, 1, 1)
        self.index = torch.zeros(len(target), device=target.device, dtype=torch.long)
        self.rows = torch.arange(len(target), device=target.device)
        self.steps = 0

    def reset(self, ids, target, index=None):
        self.buffer[:, ids] = target
        self.index[ids] = (torch.randint(5, (len(ids),), device=target.device)
                           if index is None else index)

    def advance(self, target):
        # One call per 5ms physical step, NOT one call per policy frame.
        self.buffer = torch.cat((self.buffer[1:], target.unsqueeze(0)), dim=0)
        self.steps += 1
        return self.buffer[self.index, self.rows]


def spawn_physhsi_robot(prim_path, cfg, **kwargs):
    """Preserve original URDF shapes; stage-local four cylinder->capsule edits."""
    import isaaclab.sim as sim_utils
    from pxr import Usd, UsdGeom, Gf
    prim = sim_utils.spawn_from_usd(prim_path, cfg, **kwargs)
    for root in sim_utils.find_matching_prims(prim_path):
        for child in list(Usd.PrimRange(root)):
            if child.IsInstance() and child.GetName() == 'collisions':
                child.SetInstanceable(False)
        count = 0
        for child in list(Usd.PrimRange(root)):
            if child.IsA(UsdGeom.Cylinder) and '/collisions/' in str(child.GetPath()):
                cylinder = UsdGeom.Cylinder(child)
                radius, height, axis = cylinder.GetRadiusAttr().Get(), cylinder.GetHeightAttr().Get(), cylinder.GetAxisAttr().Get()
                if axis != 'Z':
                    raise ValueError('Unexpected shoulder collision axis')
                child.SetTypeName('Capsule')
                capsule = UsdGeom.Capsule(child)
                capsule.CreateRadiusAttr().Set(radius)
                capsule.CreateHeightAttr().Set(height)
                capsule.CreateAxisAttr().Set(axis)
                capsule.CreateExtentAttr().Set([Gf.Vec3f(-radius, -radius, -height/2-radius),
                                                Gf.Vec3f(radius, radius, height/2+radius)])
                count += 1
        if count != 4:
            raise ValueError(f'Expected four G1 shoulder capsules, found {count}')
    return prim
