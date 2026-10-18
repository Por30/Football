"""Create a reversible ground-origin pickup profile without modifying the source."""
import hashlib
import json
from pathlib import Path
import shutil

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SOURCE = ROOT / 'source/perceptual_ball/perceptual_ball/assets/motions/findbox'
TARGET = SOURCE / 'ground_pickup'
manifest = json.loads((SOURCE / 'amp_manifest.json').read_text())
mapping = json.loads((SOURCE / 'filename_mapping.json').read_text())
excluded = ['pick_up/pick_up_01.pt', 'pick_up/pick_up_02.pt']
protected = [SOURCE/'amp_manifest.json', SOURCE/'filename_mapping.json'] + [SOURCE/c['file'] for c in manifest['clips']]
protected += list((ROOT/'findbox').rglob('*.pt')) + [ROOT/'findbox/amp_manifest.json']
digests = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
for row in manifest['clips']:
    assert hashlib.sha256((SOURCE/row['file']).read_bytes()).hexdigest() == row['sha256']
    if row['file'] in excluded:
        continue
    path = TARGET / row['file']
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == (SOURCE/row['file']).read_bytes()
    else:
        shutil.copy2(SOURCE/row['file'], path)
manifest['clips'] = [c for c in manifest['clips'] if c['file'] not in excluded]
manifest.update(dataset_revision=4, dataset_version='findbox_ground_pickup_v1',
    ground_reset=dict(collision_profile='g1_visual_convex_hull_full_body_v1',
                      pickup_frame_range_exclusive=[0,32],
                      evidence='docs/carrybox/wall5_ground_20261017/reset_geometry_initial_fail.json'),
    provenance=dict(source_dataset=str(SOURCE.relative_to(ROOT)),
                    source_manifest_sha256=digests[str((SOURCE/'amp_manifest.json').relative_to(ROOT))],
                    excluded_clips=excluded, selection='Keep complete native ground-origin pickup03; no frame edits',
                    record='docs/carrybox/wall5_ground_20261017/profile_record.json'))
(TARGET/'amp_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
new_mapping = dict(source_dataset=mapping['source_dataset'], source_profile=str(SOURCE.relative_to(ROOT)),
    mapping={k:v for k,v in mapping['mapping'].items() if v not in excluded},
    excluded_mapping={k:dict(preserved_file=str((SOURCE/v).relative_to(ROOT)), reason='raised pickup origin')
                      for k,v in mapping['mapping'].items() if v in excluded})
(TARGET/'filename_mapping.json').write_text(json.dumps(new_mapping, indent=2)+'\n')
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in digests.items())
record=dict(profile=str(TARGET.relative_to(ROOT)), interpretation='Complete pickup from ground, with lift frames retained; disclosed assumption, not explicit user confirmation',
    original_files_retained=True, protected_sha256=digests, excluded_clips=excluded,
    kept_pickup='pick_up/pick_up_03.pt', pickup_source_frame_range_inclusive=[0,128],
    pickup_reset_frame_range_inclusive=[0,31],
    clip_count=len(manifest['clips']), total_frames=sum(c['frames'] for c in manifest['clips']),
    manifest_sha256=hashlib.sha256((TARGET/'amp_manifest.json').read_bytes()).hexdigest())
(OUT/'profile_record.json').write_text(json.dumps(record,indent=2)+'\n')
print(record['clip_count'], record['total_frames'], record['manifest_sha256'])
