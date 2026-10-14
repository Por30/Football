"""V5 camera contract and shared simulation/deployment preprocessing (metres).

Input must already be rectified depth in its own optical frame, not RGB-aligned
range or disparity. No robot/ball segmentation or privileged state is used.
"""
import copy
import json
import math
from pathlib import Path
import torch


def load_profile(path):
    profile = json.loads(Path(path).read_text())
    required = {'schema', 'calibration_status', 'parent_link', 'position_m', 'quaternion_wxyz_world',
                'source_width', 'source_height', 'source_intrinsics', 'crop_xywh', 'width', 'height',
                'near_m', 'far_m', 'update_period_s', 'depth_unit_m', 'rectified', 'resize', 'invalid',
                'depth_semantics', 'distortion', 'history_length'}
    if not required <= profile.keys():
        raise ValueError('Incomplete camera profile: '+str(sorted(required-profile.keys())))
    if (profile['schema'] != 1 or profile['parent_link'] != 'torso_link'
            or profile['width'] != 48 or profile['height'] != 27 or profile['history_length'] != 8
            or profile['rectified'] is not True or profile['distortion'] != 'rectified_before_input'
            or profile['resize'] != 'nearest_exact' or profile['invalid'] != 'nonfinite_or_nonpositive_to_far'
            or profile['depth_semantics'] != 'optical_z_metres'
            or profile['calibration_status'] not in ('nominal_unverified', 'calibrated')):
        raise ValueError('Unsupported v5 depth profile convention/shape')
    for key in ('source_width', 'source_height'):
        if type(profile[key]) is not int or profile[key] <= 0:
            raise ValueError('Invalid source image dimensions')
    if len(profile['crop_xywh']) != 4 or any(type(x) is not int for x in profile['crop_xywh']):
        raise ValueError('Crop must contain four integers')
    x, y, w, h = profile['crop_xywh']
    if min(x, y) < 0 or min(w, h) <= 0 or x+w > profile['source_width'] or y+h > profile['source_height']:
        raise ValueError('Crop outside source image')
    k, p, q = profile['source_intrinsics'], profile['position_m'], profile['quaternion_wxyz_world']
    if len(k) != 4 or len(p) != 3 or len(q) != 4 or not all(math.isfinite(v) for v in k+p+q):
        raise ValueError('Invalid intrinsics/extrinsics')
    if min(k[:2]) <= 0 or abs(sum(v*v for v in q)-1.) > 1.e-5:
        raise ValueError('Invalid focal length or non-unit quaternion')
    for name in ('depth_unit_m', 'update_period_s', 'near_m', 'far_m'):
        if not math.isfinite(profile[name]) or profile[name] <= 0:
            raise ValueError('Invalid '+name)
    if profile['near_m'] != .1 or profile['far_m'] != 3.:
        raise ValueError('V5 feedback bounds require 0.1-3.0 m')
    if profile['calibration_status'] == 'calibrated' and not profile.get('calibration_evidence'):
        raise ValueError('Calibrated profile requires calibration_evidence')
    return profile


def target_intrinsics(profile):
    """OpenCV integer-centre K after crop and pixel-centred resize."""
    fx, fy, cx, cy = profile['source_intrinsics']
    x, y, w, h = profile['crop_xywh']
    sx, sy = profile['width']/w, profile['height']/h
    return (fx*sx, fy*sy, (cx-x+.5)*sx-.5, (cy-y+.5)*sy-.5)


def clean_depth_m(depth, near=.1, far=3.):
    valid = torch.isfinite(depth) & (depth > 0.)
    return torch.where(valid, depth, far).clamp(near, far)


def preprocess_hardware_depth(raw, profile):
    """[N,H,W] rectified device samples -> [N,27,48] optical metres.

    Caller owns capture timestamps, dropped/stale-frame policy and oldest-first
    8-frame history at policy ticks. This function does not fabricate new frames.
    """
    if raw.ndim != 3 or tuple(raw.shape[-2:]) != (profile['source_height'], profile['source_width']):
        raise ValueError('Hardware source image shape differs from camera profile')
    x, y, w, h = profile['crop_xywh']
    depth = clean_depth_m(raw.float()*profile['depth_unit_m'], profile['near_m'], profile['far_m'])
    depth = depth[:, y:y+h, x:x+w]
    return torch.nn.functional.interpolate(depth[:, None], size=(profile['height'], profile['width']),
                                            mode='nearest-exact')[:, 0]


def depth_contract(profile):
    return dict(schema=1, backend='warp_visual_mesh', geometry='all_visible_rigid_links_ball_ground_v1',
                profile=copy.deepcopy(profile), target_intrinsics=list(target_intrinsics(profile)),
                output='optical_z_metres', normalization='none', history_order='oldest_to_newest',
                feedback_gate='valid_depth_recency_and_predicted_uncertainty_not_ball_visibility')
