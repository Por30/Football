"""Decode all four panels and verify synchronized higher spectator cameras."""
from pathlib import Path
import hashlib
import json
import subprocess
import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image

DOC = Path(__file__).resolve().parent
r = json.loads((DOC/'recording.json').read_text())
video = Path(r['video'])
assert r['status'] == 'PASS' and r['num_envs'] == 4
assert r['reset_sampling'] == 'unmodified_wall11_random_hybrid'
assert r['environment_contract']['variant'] == 'walled11'
assert r['environment_contract']['reset'] == 'bernoulli80_RSI_conditional_2over3_1over6_1over6_ground_correction5mm'
assert sum(r['reset_counts']) == len(r['episodes'])
assert r['frames'] == 500 and r['steps'] == 1000
assert r['actor_depth_units'] == 'metres'
assert r['environment_contract']['actor'] == 'proprio93x6_depth4x27x48'
assert r['depth_display_mapping'] == 'uint8(255*(1-depth_m/3))_display_only'
assert len(set(r['spectator_cameras'])) == 4 and not r['rendering_advances_physics']
views = json.loads((DOC/'camera_trajectory.json').read_text())
assert len(views) == 500
for index, row in enumerate(views):
    assert row['frame'] == index+1 and row['control_step'] == 2*(index+1)
    assert [v['env_id'] for v in row['views']] == [0, 1, 2, 3]
    assert all(v['height_above_ground'] >= 5.7999 for v in row['views'])
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-i', str(video), '-f', 'null', '-'],
               check=True)
selected, variation, contrast = [], [], []
with imageio.get_reader(video, input_params=['-threads', '2']) as reader:
    meta = reader.get_meta_data()
    previous = None
    frames = 0
    for index, frame in enumerate(reader):
        assert frame.shape == (1080, 1920, 3)
        values = []
        for env_id in range(4):
            x, y = (env_id % 2)*960, (env_id // 2)*540
            # Exclude text/depth overlays when checking each scene.
            values.append(float(frame[y+105:y+400, x+100:x+780].std()))
        contrast.append(values)
        if index in (0, 24, 49, 124, 249, 374, 498, 499):
            selected.append(Image.fromarray(frame).resize((960, 540)))
        if previous is not None:
            variation.append(float(np.abs(frame.astype(np.float32)-previous).mean()))
        previous = frame.astype(np.float32)
        frames += 1
    assert frames == 500 and abs(meta['fps']-25) < 1e-6 and abs(meta['duration']-20) < .05
    assert max(variation) > 1.
    minima = np.min(contrast, axis=0)
    assert (minima > 5.).all(), minima
    sheet = Image.new('RGB', (1920, 2160))
    for i, frame in enumerate(selected):
        sheet.paste(frame, ((i % 2)*960, (i // 2)*540))
    sheet.save(video.parent/'contact_sheet.jpg', quality=90)
result = dict(status='PASS', frames=frames, fps=meta['fps'], duration=meta['duration'],
    resolution=list(meta['size']), full_decode=True, min_scene_contrast_per_panel=minima.tolist(),
    max_frame_change=max(variation), source_checkpoint_sha256=r['checkpoint_sha256'],
    video_sha256=hashlib.sha256(video.read_bytes()).hexdigest(), file_bytes=video.stat().st_size,
    four_synchronized_views=True, camera_height_at_least_m=5.7999)
(DOC/'video_validation.json').write_text(json.dumps(result, indent=2)+'\n')
print('VIDEO_CHECK_PASS', json.dumps(result))
