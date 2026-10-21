"""Reward-only geometry in metres; legacy tasks retain their original defaults.

G1 anchors: 2026-10-20 PhysX reference-pose FK with the lowest foot hull on
the ground. Walking clips are equally weighted (median of clip medians,
projected-gravity XY < 0.2). These are not dynamically settled measurements.
Evidence: docs/carrybox/wall5_semantic_20261020/geometry.json.
X2 anchors are from the supplied comparison, not measured in this repository.
"""
import math


X2_REWARD_GEOMETRY = {
    'profile': 'legacy_x2_thresholds', 'body_frame': 'torso',
    'near_distance': .7,
    'carryup_box': .64, 'success_box': .60, 'held_box': .55,
    'crouch_box': .58, 'slow_pickup_box': .55,
    'stand_pelvis': .66, 'stand_gate_low': .50, 'stand_gate_span': .16,
    'crouch_pelvis': .60, 'fallen_pelvis': .20,
    'stand_head': .85, 'success_head': .80, 'fallen_head': .40,
    'carryup_height_exp': 3., 'stand_pelvis_exp': 8., 'stand_head_exp': 8.,
}

G1_ANCHORS = {'pelvis': .7731534838676453, 'head': 1.2196258306503296,
              'box': .8507904410362244}
# User-corrected head_yaw_link anchor; motion endpoint 5 was the waist origin.
X2_ANCHORS = {'pelvis': .669, 'head': 1.112, 'box': .729}


def g1_reward_geometry():
    """Preserve X2's standing XY reach and normalized height reward curves."""
    g = dict(X2_REWARD_GEOMETRY, profile='g1_reference_geometry_v20', body_frame='pelvis')
    pelvis_scale, head_scale = G1_ANCHORS['pelvis'] / X2_ANCHORS['pelvis'], G1_ANCHORS['head'] / X2_ANCHORS['head']
    box_scale = (G1_ANCHORS['box'] - .125) / (.729 - .125)
    g['near_distance'] = math.sqrt(.7**2 - (.669-.125)**2 + (G1_ANCHORS['pelvis']-.125)**2)
    for key in ('stand_pelvis', 'stand_gate_low', 'stand_gate_span', 'crouch_pelvis', 'fallen_pelvis'):
        g[key] *= pelvis_scale
    for key in ('stand_head', 'success_head', 'fallen_head'):
        g[key] *= head_scale
    for key in ('carryup_box', 'success_box', 'held_box', 'crouch_box', 'slow_pickup_box'):
        g[key] = .125 + (g[key]-.125) * box_scale
    g['carryup_height_exp'] /= box_scale
    g['stand_pelvis_exp'] /= pelvis_scale
    g['stand_head_exp'] /= head_scale
    return g


def reward_geometry(env):
    """Opt in by configuration; wall3/4 and other callers keep old semantics."""
    return getattr(getattr(env, 'cfg', None), 'reward_geometry', X2_REWARD_GEOMETRY)
