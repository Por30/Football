"""Reproduce the authorized carrywith1 prefix/hold edit, preserving the old dataset."""
from pathlib import Path
import hashlib
import json
import os
import shutil

import torch

ROOT = Path(__file__).resolve().parents[3]
DOC = Path(__file__).resolve().parent
ACTIVE = ROOT / 'findbox'
BACKUP = DOC / 'original_dataset'
OLD_MANIFEST_HASH = 'eef4d55d77eb26b46fd1be58da628edd07920f5e02198a7636c2e83253e5cb3c'
LAST_SOURCE_FRAME = 20
OUTPUT_FRAMES = 300
VELOCITIES = {'base_linear_velocity', 'base_angular_velocity', 'joint_velocity'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest_path = ACTIVE / 'amp_manifest.json'
    assert sha(manifest_path) == OLD_MANIFEST_HASH, 'Expected the original dataset revision'
    old = json.loads(manifest_path.read_text())
    assert not BACKUP.exists(), 'Refusing to overwrite the original snapshot'
    for row in old['clips']:
        assert sha(ACTIVE / row['file']) == row['sha256']
    shutil.copytree(ACTIVE, BACKUP)
    assert sha(BACKUP / 'amp_manifest.json') == OLD_MANIFEST_HASH
    for row in old['clips']:
        assert sha(BACKUP / row['file']) == row['sha256']

    source = torch.load(BACKUP / 'carryWith/carrywith1.pt', weights_only=True, map_location='cpu')
    indices = torch.arange(OUTPUT_FRAMES).clamp(max=LAST_SOURCE_FRAME)
    edited = {}
    for name, value in source.items():
        assert isinstance(value, torch.Tensor) and value.shape[0] == 256, name
        edited[name] = value[indices].clone()
        if name in VELOCITIES:
            # Retained forward differences are valid up to frame 19; frame 20 starts the hold.
            edited[name][LAST_SOURCE_FRAME:] = 0
        assert torch.isfinite(edited[name]).all()
    staged = DOC / 'carrywith1_hold.pt'
    torch.save(edited, staged)
    new_hash = sha(staged)
    manifest = dict(old)
    manifest['clips'] = [dict(row) for row in old['clips']
                         if row['file'] not in {'carryWith/carrywith2.pt', 'carryWith/carrywith3.pt'}]
    for row in manifest['clips']:
        if row['file'] == 'carryWith/carrywith1.pt':
            row.update(frames=OUTPUT_FRAMES, sha256=new_hash)
    recipe = dict(
        dataset_revision=2, dataset_version='carrywith1_prefix_hold_v1',
        previous_manifest_sha256=OLD_MANIFEST_HASH,
        previous_dataset=str(BACKUP.relative_to(ROOT)),
        retained_source_frames=[0, LAST_SOURCE_FRAME], repeated_source_frame=LAST_SOURCE_FRAME,
        first_repeated_output_frame=LAST_SOURCE_FRAME+1,
        static_output_frames=[LAST_SOURCE_FRAME, OUTPUT_FRAMES-1],
        source_frame_indices=indices.tolist(), output_frames=OUTPUT_FRAMES, fps=60,
        duration_seconds=OUTPUT_FRAMES/60,
        zeroed_velocity_fields=sorted(VELOCITIES),
        excluded_clips=['carryWith/carrywith2.pt', 'carryWith/carrywith3.pt'],
        group_weights_unchanged=True,
    )
    manifest.update(dataset_revision=2, dataset_version=recipe['dataset_version'],
                    provenance={'previous_manifest_sha256': OLD_MANIFEST_HASH,
                                'edit_record': str((DOC/'edit_record.json').relative_to(ROOT))})
    staged_manifest = DOC / 'new_amp_manifest.json'
    staged_manifest.write_text(json.dumps(manifest, indent=2)+'\n')
    recipe.update(new_manifest_sha256=sha(staged_manifest), new_carrywith1_sha256=new_hash)
    (DOC / 'edit_record.json').write_text(json.dumps(recipe, indent=2)+'\n')

    # Publish only after the complete old dataset and the new artifacts have been checked.
    destination = ACTIVE / 'carryWith/carrywith1.pt'
    temporary = destination.with_suffix('.pt.tmp')
    shutil.copy2(staged, temporary)
    os.replace(temporary, destination)
    temporary_manifest = ACTIVE / 'amp_manifest.json.tmp'
    shutil.copy2(staged_manifest, temporary_manifest)
    os.replace(temporary_manifest, manifest_path)
    for relative in recipe['excluded_clips']:
        archived = DOC / 'excluded_from_active' / relative
        archived.parent.mkdir(parents=True, exist_ok=True)
        assert sha(ACTIVE / relative) == sha(BACKUP / relative)
        os.replace(ACTIVE / relative, archived)
    assert len(list(ACTIVE.rglob('*.pt'))) == len(manifest['clips']) == 15
    for row in manifest['clips']:
        assert sha(ACTIVE / row['file']) == row['sha256']
    print(json.dumps({k:v for k,v in recipe.items() if k != 'source_frame_indices'}, indent=2))


if __name__ == '__main__':
    main()
