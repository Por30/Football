"""Package the four-robot video after decode and manual visual inspection."""
from datetime import datetime
from pathlib import Path
import hashlib
import json
import sys

DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
OUT = ROOT/'outputs/carrybox/wall5_play4_rev22_20261022'
SLUG = 'carrybox-wall5-play4-rev22-20261022'
sys.path.insert(0, '/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter, task_contract_sha256, validate_paths

r = json.loads((DOC/'recording.json').read_text())
v = json.loads((DOC/'video_validation.json').read_text())
s = json.loads((DOC/'selection.json').read_text())
receipts = json.loads((DOC/'receipts.json').read_text())['tests']
review = (DOC/'visual_review.txt').read_text().strip()
assert r['status'] == v['status'] == 'PASS' and review
assert all(t['result'] == 'PASS' for t in receipts)
assert hashlib.sha256(Path(r['checkpoint']).read_bytes()).hexdigest() == r['checkpoint_sha256']
for name, expected in s['source_sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
cmdline = Path(f'/proc/{s["training_pid"]}/cmdline')
actual = ([a.decode() for a in cmdline.read_bytes().split(b'\0') if a]
          if cmdline.exists() else None)
ticks = (Path(f'/proc/{s["training_pid"]}/stat').read_text().split(') ',1)[1].split()[19] if actual else None)
status = dict(checked_at=datetime.now().astimezone().isoformat(), training_pid=s['training_pid'],
              command=actual, same_process_running=actual == s['training_command'] and ticks == s['training_start_ticks'], process_modified=False)
(DOC/'formal_status.json').write_text(json.dumps(status, indent=2)+'\n')

rows = ['| 机器人 | 参考起点 | reset次数 | 原因 | 窗口末回合已执行 |',
        '|---|---|---:|---|---:|']
for i in range(4):
    events = [e for e in r['episodes'] if e['env_id'] == i]
    counts = {key: sum(e[key] for e in events) for key in ('tipped', 'fell', 'timeout')}
    why = ', '.join(f'{key}={value}' for key, value in counts.items())
    rows.append(f'| {i+1} | {"空手/地面箱" if i<3 else "持箱参考"} | {len(events)} | {why} | '
                f'{r["final_censored"][i]["steps"]*.02:.2f}s |')
summary = (f'录制model_{r["checkpoint_iteration"]}.pt，4环境同步20秒、1920×1080/25fps四宫格，'
           f'旁观相机基准高度5.8m（沿用上一段高位镜头）。保留默认3个loco/地面箱起点和1个明确标注的hold参考起点。'
           f'每个机器人reset次数分别为{r["reset_counts"]}，没有裁剪失败片段。')
video_name = Path(r['video']).name
text = f'''# Wall5 最新checkpoint：四机器人高位镜头

选取时最新完整模型：`{r['checkpoint']}`，revision22。选取时间{s['selected_at']}；录制期间训练继续推进，本视频固定使用该模型。

[观看20秒MP4](../../../outputs/carrybox/wall5_play4_rev22_20261022/{video_name}) · [关键帧拼图](../../../outputs/carrybox/wall5_play4_rev22_20261022/contact_sheet.jpg)

{summary}

同一次play创建4个环境，统一批量策略推理和50Hz物理控制；每两个控制步，四台独立旁观相机同时渲染同一物理时刻，合成一帧四宫格。不是四次回放拼接；所有自动reset均保留。每格960×540，合成1920×1080，25fps/500帧/20秒。

相机跟随各自机器人与箱子的中点，从墙的对侧俯视。目标高0.6m、镜头高偏移5.2m、水平偏移3.6m，因此基准镜头距地5.8m；机器人远离箱子时按距离扩大取景。焦距30mm、水平aperture20.955mm。每帧检查渲染前后物理时间、控制步计数与机器人位置完全一致。实际相机轨迹见camera_trajectory.json。

**前三格为空手起点，第四格为持箱参考初始化。第四格开场已有箱子不代表学会了从地面抱起。** 保留任务的固定RSI配额[0,0,0,2]、原13m环境间距、碰撞/墙/圆柱/深度噪声与遮挡。每格右下角显示对应actor收到的最新米制深度帧，0.1–3m仅为灰度显示映射除3，策略输入仍为米；旁观相机位置不影响actor输入。

严格核对完整环境契约并加载原权重，恢复checkpoint第{r['checkpoint_iteration']}轮的yaw课程{r['yaw_degrees']:.2f}°、增量推扰强度{r['push_scale']:.2f}；seed42、均值动作、无训练/优化器更新。

## 表现与回合

{review}

{chr(10).join(rows)}

这是四个环境的一段回放，不作为成功率评估；持箱参考起点需与地面拾箱分开理解。

完整解码与四格主画面检查PASS：{v['frames']}帧、{v['duration']}秒，文件约{v['file_bytes']/1024/1024:.2f}MiB。源代码/模型hash和模型权重不变。后台PID{s['training_pid']}在{status['checked_at']}核对仍为原命令={status['same_process_running']}，本次未停止、重启或调参。

[选择记录](selection.json)、[回合和配置](recording.json)、[轨迹](trajectory.json)、[相机轨迹](camera_trajectory.json)、[视频检查](video_validation.json)、[执行回执](receipts.json)。

复现命令（已有视频不会被覆盖；再次录制需新目录）：

```bash
cd /home/cao/perceptual_ball
bash docs/carrybox/wall5_play4_rev22_20261022/record_and_check.sh
```
'''
(DOC/'README.md').write_text(text)
(OUT/'README.md').write_text(f'# Wall5 model{r["checkpoint_iteration"]} 四机器人高位回放\n\n'
    f'[观看20秒MP4]({video_name}) · [关键帧拼图](contact_sheet.jpg)\n\n'+review+
    '\n\n前三格为空手起点，第四格为持箱参考起点。'
    '\n\n[完整记录](../../../docs/carrybox/wall5_play4_rev22_20261022/README.md)。\n')
for name, prefix in (('projects/README.md', '../'), ('projects/findbox/README.md', '../../')):
    p = ROOT/name
    title, body = p.read_text().split('\n', 1)
    link = prefix+'docs/carrybox/wall5_play4_rev22_20261022/README.md'
    assert link not in body
    p.write_text(title+'\n\n'+f'2026-10-22：[wall5最新model{r["checkpoint_iteration"]}四机器人高位录像]({link})：'
                 +summary+review+' 正式训练保持运行；未作成功率评估。\n'+body)
task, _ = load_frontmatter(ROOT/f'agent/task/{SLUG}.md')
changed = [str(p.relative_to(ROOT)) for directory in (DOC, OUT) for p in directory.rglob('*')
           if p.is_file() and '__pycache__' not in p.parts]
changed += [f'agent/{kind}/{SLUG}.md' for kind in ('plan', 'task', 'report', 'handoff')]
changed += ['projects/README.md', 'projects/findbox/README.md',
            str((DOC/'artifact_validation.json').relative_to(ROOT))]
meta = dict(task_id=SLUG, language='zh-CN', axes=['L'], risk_tier='T1', status='DONE',
            changed_files=sorted(set(changed)), task_contract_sha256=task_contract_sha256(task),
            tests=receipts, resume_command=None)
for kind in ('report', 'handoff'):
    front = dict(meta, artifact=kind.upper())
    body = summary+'\n\n'+review+'\n\n四台较高旁观相机在同一物理时刻拍摄，完整视频解码和四格关键帧检查通过；'
    body += '持箱参考起点已标注，不能算地面拾箱。模型、生产任务和后台训练保持。'
    body += f'\n\n视频：{r["video"]}。详情：docs/carrybox/wall5_play4_rev22_20261022/README.md。'
    body += '现有产物不覆盖；如需再次录制，另存新目录。没有待恢复工作。\n'
    (ROOT/f'agent/{kind}/{SLUG}.md').write_text('---\n'+'\n'.join(
        k+': '+json.dumps(v, ensure_ascii=False) for k, v in front.items())+'\n---\n\n'+body)
validation = validate_paths(*(ROOT/f'agent/{kind}/{SLUG}.md' for kind in ('plan', 'task', 'report', 'handoff')))
(DOC/'artifact_validation.json').write_text(json.dumps(validation, indent=2)+'\n')
assert validation['valid'], validation
print(summary)
print(json.dumps(status))
print(json.dumps(validation))
