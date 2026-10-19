from pathlib import Path
import json,hashlib,subprocess
import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parent;r=json.loads((p/'recording.json').read_text());video=Path(r['video'])
assert r['status']=='PASS' and r['frames']==500 and r['steps']==1000 and r['environment_contract']['migration_revision']==14
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-i',str(video),'-f','null','-'],check=True)
with imageio.get_reader(video,input_params=['-threads','2']) as reader:
 meta=reader.get_meta_data();frames=0;variation=[];selected=[];previous=None
 for i,frame in enumerate(reader):
  assert frame.shape==(720,1280,3)
  if i in (0,24,49,124,249,374,498,499):selected.append(Image.fromarray(frame).resize((640,360)))
  if previous is not None:variation.append(float(np.abs(frame.astype(float)-previous).mean()))
  previous=frame.astype(float);frames+=1
 assert frames==500 and abs(meta['fps']-25)<1e-6 and abs(meta['duration']-20)<.05 and max(variation)>1.
 contact=Image.new('RGB',(1280,1440));
 for i,frame in enumerate(selected):contact.paste(frame,((i%2)*640,(i//2)*360))
 contact.save(video.parent/'contact_sheet.jpg',quality=90)
result=dict(status='PASS',frames=frames,fps=meta['fps'],duration=meta['duration'],resolution=list(meta['size']),
 video_sha256=hashlib.sha256(video.read_bytes()).hexdigest(),file_bytes=video.stat().st_size,full_decode=True,
 max_frame_change=max(variation),source_checkpoint_sha256=r['checkpoint_sha256'])
(p/'video_validation.json').write_text(json.dumps(result,indent=2)+'\n');print('VIDEO_CHECK_PASS',json.dumps(result))
