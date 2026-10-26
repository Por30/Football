"""Decode the whole demo and check identity, timing, finite playback and visible frames."""
import hashlib
import json
from pathlib import Path
import subprocess
import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

doc = Path(__file__).resolve().parent
r = json.loads((doc / 'recording.json').read_text())
s = json.loads((doc / 'selection.json').read_text())
video = Path(r['video'])
assert r['status'] == 'PASS' and r['strict_load'] and r['weights_unchanged'] and r['finite_inference']
assert r['checkpoint_sha256'] == s['checkpoint_sha256'] == hashlib.sha256(Path(s['checkpoint']).read_bytes()).hexdigest()
assert r['steps'] == 1500 and r['frames'] == 750 and r['num_envs'] == 1
assert not r['rendering_advances_physics'] and not r['task_overrides'] and r['raw_continuous']
assert r['course']['speed'] == [.4, 6.] and abs(r['course']['target_half_width'] - .2) < 1.e-6
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-i', str(video), '-f', 'null', '-'], check=True)
indices = (0, 24, 49, 124, 249, 374, 499, 624, 749)
sheet = Image.new('RGB', (1440, 858), (25, 30, 36))
changes, contrasts = [], []
with imageio.get_reader(str(video), input_params=['-threads', '2']) as reader:
    meta = reader.get_meta_data()
    previous = None
    n = 0
    for i, frame in enumerate(reader):
        assert frame.shape == (1080, 1920, 3)
        scene = frame[150:950, 350:1600:4].astype(np.float32)
        contrasts.append(float(scene.std()))
        if previous is not None:
            changes.append(float(np.abs(scene - previous).mean()))
        previous = scene
        if i in indices:
            j = indices.index(i)
            x, y = (j % 3) * 480, (j // 3) * 286
            sheet.paste(Image.fromarray(frame).resize((480, 270)), (x, y))
            ImageDraw.Draw(sheet).text((x + 8, y + 272), f'{(i + 1) / 25:.2f} s', fill='white')
        n += 1
assert n == 750 and meta['fps'] == 25. and abs(meta['duration'] - 30.) < .05
assert min(contrasts) > 5. and max(changes) > .2
sheet.save(video.parent / 'contact_sheet.jpg', quality=92)
result = dict(status='PASS', frames=n, fps=meta['fps'], duration=meta['duration'],
              resolution=list(meta['size']), full_decode=True, codec=meta.get('codec'),
              min_scene_contrast=min(contrasts), max_frame_change=max(changes),
              video_sha256=hashlib.sha256(video.read_bytes()).hexdigest(), file_bytes=video.stat().st_size)
(doc / 'video_validation.json').write_text(json.dumps(result, indent=2) + '\n')
print('VIDEO_CHECK_PASS', json.dumps(result))
