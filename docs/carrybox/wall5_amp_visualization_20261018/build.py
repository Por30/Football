"""CPU-only current Wall5 AMP presentation from hash-identical native G1 recordings."""
from pathlib import Path
from datetime import datetime
import argparse,hashlib,json,re,subprocess,html
import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];DOC=Path(__file__).resolve().parent
OUT=ROOT/'outputs/carrybox/wall5_amp_20261018'
DATA=ROOT/'source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup'
OLD=ROOT/'outputs/carrybox/findbox_hold_20261014'
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
GROUP_NAMES={'pickUp':'地面拾箱','carryWith':'持箱','loco_direction':'行走'}
LABELS={'stand_to_walk_01':'站立到行走','walk_to_stand_01':'行走到站立 1','walk_to_stand_02':'行走到站立 2',
'walk_forward_01':'向前行走','walk_turn_around_01':'行走转身','walk_turn_left_045':'行走左转 45°',
'walk_turn_left_090':'行走左转 90°','walk_turn_left_135':'行走左转 135°','walk_turn_right_045':'行走右转 45°',
'walk_turn_right_090':'行走右转 90°','walk_turn_right_135':'行走右转 135°','pick_up_03':'从地面拾起箱子','hold_box_01':'持箱保持'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def identity():
    import torch
    torch.set_num_threads(1)
    launch=json.loads((ROOT/'docs/carrybox/wall5_fresh_20261018/launch.json').read_text())
    pid=launch['pid'];cmd=Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0',b' ').decode()
    assert launch['run_name'] in cmd and '--num_envs 4096' in cmd
    runs=list((ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5').glob('*_'+launch['run_name']));assert len(runs)==1
    run=runs[0]
    for file,key in [('agent.yaml','amp_data_dir'),('env.yaml','reference_motion_dataset')]:
        text=(run/'params'/file).read_text();match=re.search(r'^\s*'+key+r': (.+)$',text,re.M)
        assert match and Path(match[1]).resolve()==DATA
    model=torch.load(run/'model_0.pt',map_location='cpu',weights_only=False)
    assert model['amp']['dataset']['manifest_sha256']==sha(DATA/'amp_manifest.json')
    assert model['amp']['config']['frame_dim']==60 and model['environment_contract']['reset_probs']==[.8,0.,.2]
    return dict(pid=pid,command=cmd,run=str(run),checkpoint_identity=str(run/'model_0.pt'),
                checked_at=datetime.now().astimezone().isoformat(),amp_frame_dim=60,reset_probabilities=[.8,0.,.2])
def build():
    assert not (OUT/'index.json').exists(),'Output already exists; verify it instead'
    OUT.mkdir(exist_ok=True);run=identity();manifest=json.loads((DATA/'amp_manifest.json').read_text())
    assert len(manifest['clips'])==13 and sum(c['frames'] for c in manifest['clips'])==3785
    prior=json.loads((OLD/'recording.json').read_text());sources={c['source_sha256']:c for c in prior['clips']}
    assert prior['fps']==60 and prior['source_frame_step']==1
    rows=sorted(manifest['clips'],key=lambda c:({'pickUp':0,'carryWith':1,'loco_direction':2}[c['group']],c['file']))
    font=ImageFont.truetype(FONT,22);small=ImageFont.truetype(FONT,15);foot=ImageFont.truetype(FONT,15)
    entries=[];total=0
    for number,row in enumerate(rows,1):
        assert sha(DATA/row['file'])==row['sha256'];old=sources[row['sha256']]
        assert old['source_frames']==old['video_frames']==row['frames'] and old['source_frame_first']==0 and old['source_frame_last']==row['frames']-1
        source=OLD/old['video'];relative=Path(row['file']).with_suffix('.mp4');target=OUT/relative
        target.parent.mkdir(exist_ok=True);assert not target.exists()
        label=LABELS[Path(row['file']).stem];group=GROUP_NAMES[row['group']]
        header=Image.new('RGB',(960,64),(15,23,35));draw=ImageDraw.Draw(header)
        draw.text((18,4),f'WALL5 AMP   {number:02d}/13   {label}',font=font,fill=(243,247,251))
        draw.text((18,36),row['file'],font=small,fill=(150,197,223))
        footer=Image.new('RGB',(960,30),(15,23,35));draw=ImageDraw.Draw(footer)
        note='原生60帧/秒 · 1倍速 · 数据集运动学回放；箱体朝向/参考支撑为示意'
        if row['group']=='carryWith':note='持箱：原始0–20帧，之后重复第20帧至5秒 · 数据集运动学回放'
        draw.text((16,3),note,font=foot,fill=(199,213,227))
        with imageio.get_reader(source,input_params=['-threads','2']) as reader, imageio.get_writer(target,fps=60,codec='libx264',quality=8,pixelformat='yuv420p',macro_block_size=16,ffmpeg_params=['-threads','2','-movflags','+faststart']) as writer:
            meta=reader.get_meta_data();assert meta['size']==(960,720) and meta['fps']==60
            count=0
            for native,frame in enumerate(reader):
                assert frame.shape==(720,960,3)
                canvas=Image.fromarray(frame);canvas.paste(header,(0,0));canvas.paste(footer,(0,690));d=ImageDraw.Draw(canvas)
                timing=f'{native:03d}/{row["frames"]-1}  {native/60:5.2f}s'
                d.text((755,37),timing,font=small,fill=(200,220,235))
                d.rectangle((0,686,959,689),fill=(35,47,62));d.rectangle((0,686,int(959*(native+1)/row['frames']),689),fill=(74,196,190))
                writer.append_data(np.asarray(canvas));count+=1
                if native==row['frames']//2:canvas.save(target.with_suffix('.png'))
        assert count==row['frames']
        entry=dict(file=row['file'],label=label,group=row['group'],group_name=group,video=relative.as_posix(),preview=relative.with_suffix('.png').as_posix(),
            source_sha256=row['sha256'],source_frames=row['frames'],video_frames=count,first_frame=total,last_frame=total+count-1,
            start_seconds=total/60,end_seconds=(total+count)/60,source_video=str(source.relative_to(ROOT)),source_video_sha256=sha(source),
            amp_group_probability=manifest['groups'][row['group']])
        total+=count;entries.append(entry);print(f'EXPORTED {number}/13 {relative} frames={count}',flush=True)
    concat=OUT/'concat.txt';concat.write_text(''.join("file '"+c['video']+"'\n" for c in entries))
    chapters=OUT/'chapters.ffmeta';text=';FFMETADATA1\ntitle=Wall5 AMP ground_pickup 13 clips\n'
    for c in entries:
        text+=f'\n[CHAPTER]\nTIMEBASE=1/60000\nSTART={c["first_frame"]*1000}\nEND={(c["last_frame"]+1)*1000}\ntitle={c["label"]} - {c["file"]}\n'
    chapters.write_text(text)
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-n','-f','concat','-safe','0','-i',str(concat),'-i',str(chapters),'-map','0:v','-map_metadata','1','-map_chapters','1','-c','copy','-movflags','+faststart',str(OUT/'wall5_amp_all.mp4')],check=True)
    record=dict(dataset_path=str(DATA.relative_to(ROOT)),manifest_sha256=sha(DATA/'amp_manifest.json'),fps=60,total_frames=total,duration_seconds=total/60,
        resolution=[960,720],groups=manifest['groups'],training=run,video='wall5_amp_all.mp4',clips=entries,
        provenance='Reused G1 native 60fps kinematic recordings matched by exact PT SHA-256; only titles/footers re-encoded; all native frames retained.',
        display=prior['display_transform'],box_display=prior['box_display'],support_display=prior['support_display'],not_policy_rollout=True)
    dump(OUT/'index.json',record)
    write_overview(record);write_index(record)
    print('BUILD_COMPLETE',OUT,flush=True)
def write_overview(record):
    font=ImageFont.truetype(FONT,24);small=ImageFont.truetype(FONT,18)
    sheet=Image.new('RGB',(1320,1090),(15,23,35));d=ImageDraw.Draw(sheet)
    d.text((20,12),'Wall5 AMP · 13段参考动作 · 行走11 / 拾箱1 / 持箱1',font=font,fill='white')
    for i,c in enumerate(record['clips']):
        thumb=Image.open(OUT/c['preview']).crop((0,64,960,686));thumb.thumbnail((310,208))
        x=10+(i%4)*330;y=62+(i//4)*255
        sheet.paste(thumb,(x,y));d.text((x+3,y+208),f'{i+1:02d}  {c["label"]}',font=small,fill=(200,220,235))
        d.text((x+3,y+232),f'{c["source_frames"]}帧 / {c["source_frames"]/60:.2f}秒',font=ImageFont.truetype(FONT,14),fill=(143,173,194))
    sheet.save(OUT/'overview.png')
def write_index(record):
    cards=''.join(f'<button data-src="{c["video"]}" data-title="{html.escape(c["label"])}"><img src="{c["preview"]}" alt="{html.escape(c["label"])}"><b>{i+1:02d} · {c["label"]}</b><small>{c["source_frames"]} 帧 / {c["source_frames"]/60:.2f} 秒</small></button>' for i,c in enumerate(record['clips']))
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wall5 AMP 数据集</title><style>body{margin:0;background:#101823;color:#eaf2fa;font:16px system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:28px}h1{margin-bottom:8px}p{color:#abc2d6;line-height:1.7}video{width:100%;max-height:70vh;background:#000;border-radius:12px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}button{background:#1c2c3d;color:#eaf2fa;border:1px solid #36526b;border-radius:10px;padding:8px;text-align:left;cursor:pointer}button:hover{border-color:#64d8c6}img{width:100%;border-radius:6px}b,small{display:block;margin:5px}a{color:#6fdacb}</style><main><h1>Wall5 当前 AMP 数据集</h1><p>13段 · 3785帧 · 63.08秒 · 原生60fps / 1倍速<br>AMP采样：行走40% / 拾箱40% / 持箱20%；RSI：行走80% / 拾箱0% / 持箱20%。</p><h2 id="now">完整回放</h2><video id="player" controls preload="metadata" src="wall5_amp_all.mp4" poster="pick_up/pick_up_03.png"></video><p><button data-src="wall5_amp_all.mp4" data-title="完整回放">播放全部13段</button> <a href="wall5_amp_all.mp4" download>下载完整MP4</a> · <a href="README.md">片段时间索引与来源</a></p><div class="grid">'''+cards+'''</div><p>G1参考动作运动学回放，非训练策略表现。复用与当前PT哈希一致的既有逐帧画面；箱体朝向和参考支撑为示意。拾箱保留从地面开始的完整抬起过程；持箱前21帧为原动作，之后重复第20帧至5秒。</p></main><script>const v=document.getElementById('player');document.querySelectorAll('button[data-src]').forEach(b=>b.onclick=()=>{v.src=b.dataset.src;document.getElementById('now').textContent=b.dataset.title;v.play();v.scrollIntoView({behavior:'smooth',block:'start'})});</script></html>'''
    (OUT/'index.html').write_text(page)
    lines=['# Wall5 当前AMP数据集可视化','', '[打开浏览页](index.html) · [完整MP4](wall5_amp_all.mp4) · [缩略图总览](overview.png)','',
        '当前正式run使用`assets/motions/findbox/ground_pickup/`，13段、3785帧、60Hz，完整视频63.083秒。AMP采样行走/拾箱/持箱=40/40/20；RSI=80/0/20。','',
        '| 起点（秒） | 动作 | 文件 | 帧数 |','|---:|---|---|---:|']
    for c in record['clips']:lines.append(f'| {c["start_seconds"]:.3f} | {c["label"]} | [{c["file"]}]({c["video"]}) | {c["source_frames"]} |')
    lines+=['','画面来源：`outputs/carrybox/findbox_hold_20261014/`，逐段源PT SHA-256与当前13段完全匹配。未重新运行GPU仿真；保留所有原生帧，更换规范文件名/标题/页脚。原旧15段及训练数据均未改。','',
        '这是G1数据集运动学回放，不是训练策略表现；机器人root/joints使用原记录，箱子位置来自base_position+box_pos_local。数据未记录箱子旋转，显示yaw借用机器人yaw；参考支撑为旧录像推算的示意。它不展示wall5 reset的足部修正、随机障碍或深度观测。','',
        '地面拾箱03保留完整129帧抬起过程；高处拾箱01/02已不在当前profile。持箱01为原始0–20帧，之后重复第20帧至300帧（5秒）。逐帧元数据及复用来源见[index.json](index.json)。']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
def verify():
    r=json.loads((OUT/'index.json').read_text());m=json.loads((DATA/'amp_manifest.json').read_text())
    assert sha(DATA/'amp_manifest.json')==r['manifest_sha256'];assert set(c['file'] for c in r['clips'])==set(c['file'] for c in m['clips'])
    assert r['fps']==60 and len(r['clips'])==13 and r['total_frames']==3785
    keyframes={};count_all=0;max_mad=0.
    for c in r['clips']:
        assert sha(DATA/c['file'])==c['source_sha256']
        source=ROOT/c['source_video'];assert sha(source)==c['source_video_sha256']
        count=0;keys={0,c['source_frames']//2,c['source_frames']-1}
        with imageio.get_reader(OUT/c['video'],input_params=['-threads','2']) as reader, imageio.get_reader(source,input_params=['-threads','2']) as original:
            meta=reader.get_meta_data();assert meta['fps']==60 and meta['size']==(960,720)
            for n,f in enumerate(reader):
                assert f.shape==(720,960,3)
                if n in keys:
                    assert f[70:680].std()>10
                    old=original.get_data(n);mad=float(np.abs(f[70:680].astype(np.float32)-old[70:680]).mean());assert mad<4.,(c['file'],n,mad)
                    max_mad=max(max_mad,mad);keyframes[c['first_frame']+n]=sha_bytes(f)
                count+=1
        assert count==c['source_frames']==c['video_frames'];assert c['first_frame']==count_all;count_all+=count
    count=0
    with imageio.get_reader(OUT/r['video'],input_params=['-threads','2']) as reader:
        meta=reader.get_meta_data();assert meta['fps']==60 and meta['size']==(960,720)
        for n,f in enumerate(reader):
            if n in keyframes:assert sha_bytes(f)==keyframes[n],('concat mismatch',n)
            count+=1
    assert count==count_all==3785
    assert len(list(OUT.rglob('*.mp4')))==14
    live=identity()
    result=dict(status='PASS',checked_at=datetime.now().astimezone().isoformat(),clips=13,decoded_clip_frames=count_all,decoded_overview_frames=count,
                fps=60,duration_seconds=count/60,all_data_hashes_match=True,source_frame_pixel_max_mean_abs_error=max_mad,
                overview_keyframes_match_clips=True,training_pid=live['pid'],training_process_untouched=True)
    dump(OUT/'verification.json',result);print(json.dumps(result,ensure_ascii=False))
def sha_bytes(array):return hashlib.sha256(array.tobytes()).hexdigest()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');args=p.parse_args()
    verify() if args.verify_only else build()
