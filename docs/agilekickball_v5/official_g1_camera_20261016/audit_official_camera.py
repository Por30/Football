"""Offline check of vendor source facts, default profile and 60/50 Hz evidence."""
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT/'scripts/sim2sim'))
from scene_depth import DEFAULT_PROFILE, camera_contract

sources = json.loads((HERE/'official_sources.json').read_text())
p = camera_contract.load_profile(DEFAULT_PROFILE, allow_subpolicy_capture=True)
routine, urdf, diagram = [sources[k] for k in ('official_routine','official_urdf','official_fov_diagram')]
assert (p['source_width'],p['source_height'],p['source_fps'],p['source_format']) == (
    routine['example_depth_width'],routine['example_depth_height'],routine['example_depth_fps'],routine['example_depth_format'])
assert p['source_camera_model'].endswith(routine['camera_model'])
assert p['parent_link'] == urdf['parent']
np.testing.assert_array_equal(p['position_m'], urdf['position_m'])
r, pitch, yaw = urdf['rpy_rad']
assert r == yaw == 0
expected_q = [math.cos(pitch/2),0.,math.sin(pitch/2),0.]
np.testing.assert_allclose(p['quaternion_wxyz_world'],expected_q,rtol=0,atol=1.e-14)
assert abs(math.degrees(pitch)-(90.-diagram['optical_axis_from_vertical_deg'])) < 1.e-10
vfov = math.degrees(2*math.atan(p['source_height']/(2*p['source_intrinsics'][1])))
assert abs(vfov-diagram['vertical_fov_deg']) < 1.e-10
assert p['crop_xywh'] == [0,0,640,480]
assert p['update_period_s'] == 1/routine['example_depth_fps']
assert p['calibration_status'] == 'nominal_unverified' and p['calibration_evidence'] is None
legacy = ROOT/'docs/agilekickball_v5/camera_nominal.json'
assert hashlib.sha256(legacy.read_bytes()).hexdigest() == sources['legacy_profile_sha256']
try:
    camera_contract.load_profile(DEFAULT_PROFILE)
except ValueError:
    pass
else:
    raise AssertionError('Lazy 50 Hz training must not silently accept a 60 Hz profile')

smoke = json.loads((HERE/'smoke.json').read_text())
assert smoke['interface_smoke_pass'] and smoke['errors'] == []
assert smoke['steps'] == 100
assert smoke['depth_captures'] == 121  # includes both t=0 and t=2 seconds
assert smoke['depth_missed_scheduled_frames'] == 0
assert len(smoke['depth_policy_samples']) == 100
assert smoke['depth_unique_consumed_frames'] == 100
assert smoke['depth_overwritten_before_consumption'] == 20
np.testing.assert_allclose(smoke['depth_scheduled_capture_times_s'], np.arange(121)/60, rtol=0,atol=1.e-10)
assert smoke['depth_max_quantization_delay_s'] <= smoke['physics_dt']+1.e-9
assert smoke['depth_max_policy_frame_age_s'] < p['update_period_s']+smoke['physics_dt']+1.e-9
assert all(c['actual_time_s']+1.e-9 >= c['scheduled_time_s'] for c in smoke['depth_capture_events'])
assert all(s['capture_time_s'] <= s['policy_time_s']+1.e-9 for s in smoke['depth_policy_samples'])
result = dict(official_profile_checks='PASS',sensor='D435i',stream='640x480 Z16 60fps (official example)',
    vertical_fov_deg=vfov,mount_pitch_deg=math.degrees(pitch),policy_resolution=[48,27],policy_hz=50,
    actual_captures=121,endpoint='t=0 and t=2 included',policy_consumptions=100,
    unique_consumed_frames=100,overwritten_before_consumption=20,pending_final_frame=1,
    missed_scheduled_frames=0,max_physics_quantization_delay_s=smoke['depth_max_quantization_delay_s'],
    max_policy_frame_age_s=smoke['depth_max_policy_frame_age_s'],legacy_profile_unchanged=True,
    calibration_status=p['calibration_status'],intrinsics='nominal derived K; hardware get_intrinsics() still required')
(HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
