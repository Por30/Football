"""Make a bounded-bitrate viewing copy; retain the complete original recording."""
import hashlib
import json
import subprocess
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg

doc = Path(__file__).resolve().parent
source = Path(json.loads((doc / 'recording.json').read_text())['video'])
target = source.with_name(source.stem + '_preview.mp4')
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
command = [ffmpeg, '-nostdin', '-n', '-v', 'error', '-i', str(source),
           '-c:v', 'libx264', '-preset', 'fast', '-crf', '24', '-maxrate', '8M',
           '-bufsize', '16M', '-pix_fmt', 'yuv420p', '-threads', '2',
           '-movflags', '+faststart', str(target)]
subprocess.run(command, check=True)
subprocess.run([ffmpeg, '-v', 'error', '-i', str(target), '-f', 'null', '-'], check=True)
with imageio.get_reader(target, input_params=['-threads', '2']) as reader:
    meta = reader.get_meta_data()
    count = sum(1 for _ in reader)
assert count == 500 and meta['size'] == (1920, 1080)
assert meta['fps'] == 25 and abs(meta['duration'] - 20) < .05
(doc / 'delivery.json').write_text(json.dumps(dict(status='PASS', video=str(target),
    original=str(source), encode_command=command, frames=count, fps=meta['fps'],
    duration=meta['duration'], resolution=list(meta['size']), full_decode=True,
    bytes=target.stat().st_size, sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    timeline='All 500 frames retained; no trimming, retiming or frame interpolation.'), indent=2) + '\n')
print(target)
