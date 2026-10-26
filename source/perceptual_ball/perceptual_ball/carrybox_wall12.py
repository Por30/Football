"""Training-only camera-frame pose supervision for variable-size untextured boxes."""
from functools import lru_cache
from itertools import permutations, product
import torch


POSE_CONTRACT = dict(schema=1, frame='camera_optical_xright_ydown_zforward', units='metres',
    target='xyz3_rotation_first_two_columns6_physical_size3', target_dim=12, prediction_dim=9,
    symmetry='right_multiply_size_preserving_proper_signed_permutations',
    size_atol_m=1.e-6, size_rtol=1.e-5,
    pairing='same_capture_latest_noisy_depth_reset_invalidated',
    supervision='all_current_frames_first_Tminus1_no_visibility_or_distance_mask',
    loss='position_mse_plus_min_equivalent_rotation6_mse', actor_feedback=False)


@lru_cache(maxsize=None)
def box_rotations(device, dtype):
    """24 proper axis permutations; a specific cuboid permits only a subset."""
    matrices = []
    for axes in permutations(range(3)):
        parity = (-1) ** sum(axes[i] > axes[j] for i in range(3) for j in range(i+1, 3))
        for signs in product((-1, 1), repeat=3):
            if parity * signs[0] * signs[1] * signs[2] == 1:
                matrices.append([[signs[i] if axes[i] == j else 0 for j in range(3)] for i in range(3)])
    with torch.inference_mode(False):
        return torch.tensor(matrices, device=device, dtype=dtype)


def box_symmetry_mask(sizes, rotations):
    # A signed permutation only reorders dimensions. GEMM may round them under
    # TF32 at training batch sizes and incorrectly reject even the identity.
    transformed = sizes[:, rotations.abs().argmax(dim=-1)]
    return (torch.isclose(transformed, sizes[:, None], atol=1.e-6, rtol=1.e-5).all(-1)
            & (sizes > 0).all(-1, keepdim=True))


def box_pose_loss(prediction, target):
    """Predict xyz + first two rotation columns; size is a label, never an input."""
    if prediction.ndim != 2 or target.shape != (len(prediction), 12) or prediction.shape[-1] != 9:
        raise ValueError('Wall12 pose supervision requires prediction[N,9] and target[N,12]')
    target = target.detach()
    x, y = target[:, 3:6], target[:, 6:9]
    rotation = torch.stack((x, y, torch.linalg.cross(x, y)), -1)
    symmetries = box_rotations(prediction.device, prediction.dtype)
    allowed = box_symmetry_mask(target[:, 9:12], symmetries)
    candidates = rotation[:, None] @ symmetries
    candidates = candidates[..., :2].transpose(-1, -2).flatten(-2)
    error = (prediction[:, None, 3:] - candidates).square().mean(-1)
    orientation = error.masked_fill(~allowed, float('inf')).min(-1).values.mean()
    position = (prediction[:, :3] - target[:, :3]).square().mean()
    return position, orientation
