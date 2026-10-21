"""Close out the pinned inference recording after video and visual verification."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import sys

DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
OUT = ROOT / 'outputs/carrybox/wall5_play3200_v19_20261020'
slug = 'carrybox-wall5-play3200-v19-20261020'
sys.path.insert(0, '/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter, task_contract_sha256, validate_paths

r = json.loads((DOC / 'recording.json').read_text())
v = json.loads((DOC / 'video_validation.json').read_text())
selection = json.loads((DOC / 'selection.json').read_text())
receipts = json.loads((DOC / 'receipts.json').read_text())['tests']
review = (DOC / 'visual_review.txt').read_text().strip()
assert review and r['status'] == v['status'] == 'PASS'
assert all(t['result'] == 'PASS' for t in receipts)
for path, expected in selection['source_sha256'].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
assert hashlib.sha256(Path(r['checkpoint']).read_bytes()).hexdigest() == r['checkpoint_sha256']

pid = selection['training_pid']
cmdline = Path(f'/proc/{pid}/cmdline')
status = dict(checked_at=datetime.now().astimezone().isoformat(), training_pid=pid,
              cmdline=cmdline.read_bytes().replace(b'\0', b' ').decode() if cmdline.exists() else None,
              process_modified=False)
(DOC / 'formal_status.json').write_text(json.dumps(status, indent=2) + '\n')
episodes = r['episodes']
rows = ['| 回合 | 时长 | 结束原因 |', '|---|---:|---|']
for i, e in enumerate(episodes):
    reasons = [name for name in ('tipped', 'fell', 'timeout') if e[name]]
    rows.append(f"| {i+1} | {e['steps'] * .02:.2f}s / {e['steps']}步 | {', '.join(reasons)} |")
final = r['final_censored']
ending_reason = 'reset后的新起点，未执行动作' if final['steps'] == 0 else '录制结束，尚未结束回合'
rows.append(f"| 窗口末回合 | {final['steps'] * .02:.2f}s / {final['steps']}步 | {ending_reason} |")
summary = (f"完成{len(episodes)}次自动reset，窗口末回合已持续{final['steps'] * .02:.2f}秒。"
           f"记录到严格lift成功标记的完成回合数为{sum(e['success'] for e in episodes)}；"
           f"窗口末回合标记为{final['success']}。这是一段单环境视频，不是成功率评估。")
video_name = Path(r['video']).name
text = f'''# Wall5 最新 checkpoint play录像（2026-10-20）

本次选择时最新完整模型：`{r['checkpoint']}`，revision19，iteration {r['checkpoint_iteration']}。
选定时间：{selection['selected_at']}。录制期间后台可能继续生成新模型，本视频固定使用上述身份。

[观看20秒MP4](../../../outputs/carrybox/wall5_play3200_v19_20261020/{video_name}) · [关键帧拼图](../../../outputs/carrybox/wall5_play3200_v19_20261020/contact_sheet.jpg)

单环境、seed42、均值动作、50Hz控制、25fps、1280×720，1000个控制步连续录制。保留自动reset、原传感器噪声、遮挡、碰撞和推扰；没有挑选成功片段。当前固定技能配额在单环境下为loco，因此每次都从空手行走参考起点开始，箱子在地面；没有hold参考起点伪装地面拾箱。旁观相机跟随机器人与箱子中点，放在墙的对侧；右下角为actor实际最新深度历史帧，该旁观相机不进入策略。

严格核对全部checkpoint环境契约并严格加载actor/critic权重；无优化器更新、无AMP学习。按本run锚点0恢复至{r['checkpoint_iteration']}轮：箱子yaw范围{r['yaw_degrees']:.2f}°，推扰课程强度{r['push_scale']:.2f}。没有使用构造时0°/无推扰的简化环境。

## 观察与验证

{review}

{summary}

{chr(10).join(rows)}

完整视频解码检查PASS：{v['frames']}帧、{v['fps']}fps、{v['duration']:.2f}秒，约{v['file_bytes']/1024/1024:.2f}MiB。模型权重、源文件hash及checkpoint均保持不变。原后台训练PID{pid}在{status['checked_at']}检查时存活={status['cmdline'] is not None}；本次未停止或重启训练。并行渲染会暂时共享GPU资源。

[模型选择](selection.json)、[录制配置和回合](recording.json)、[逐步轨迹](trajectory.json)、[视频核验](video_validation.json)、[执行回执](receipts.json)。

本次使用rev19任务与checkpoint，保留已验证的相机跟随与深度角标，并按checkpoint迭代恢复课程；没有改变正式训练配置，历史录像保留。

复现入口（已存在的视频不会被覆盖；再次录制需另存目录）：

```bash
cd /home/cao/perceptual_ball
bash docs/carrybox/wall5_play3200_v19_20261020/record_and_check.sh
```
'''
(DOC / 'README.md').write_text(text)
(OUT / 'README.md').write_text(f'# Wall5 model{r["checkpoint_iteration"]} play\n\n[观看20秒MP4]({video_name}) · [关键帧](contact_sheet.jpg)\n\n' + review + '\n\n[完整记录](../../../docs/carrybox/wall5_play3200_v19_20261020/README.md)。\n')
note = (f'2026-10-20：[wall5最新model{r["checkpoint_iteration"]}的20秒play录像](LINK)：revision19、单环境loco配额、均值动作、原课程yaw{r["yaw_degrees"]:.1f}°/推扰{r["push_scale"]:.2f}，严格契约/权重核对、500帧完整解码及关键帧检查通过。' + review + ' 正式训练进程保持，视频不作成功率结论。')
for name, link in [('projects/README.md', '../docs/carrybox/wall5_play3200_v19_20261020/README.md'), ('projects/findbox/README.md', '../../docs/carrybox/wall5_play3200_v19_20261020/README.md')]:
    p = ROOT / name
    content = p.read_text()
    if link not in content:
        heading, body = content.split('\n', 1)
        p.write_text(heading + '\n\n' + note.replace('LINK', link) + '\n' + body)
task, _ = load_frontmatter(ROOT / f'agent/task/{slug}.md')
changed = [str(path.relative_to(ROOT)) for directory in (DOC, OUT)
           for path in directory.rglob('*') if path.is_file() and '__pycache__' not in path.parts]
changed += [f'agent/{kind}/{slug}.md' for kind in ('plan','task','report','handoff')]
changed += ['projects/README.md', 'projects/findbox/README.md',
            str((DOC/'artifact_validation.json').relative_to(ROOT))]
common = dict(task_id=slug, language='zh-CN', axes=['L'], risk_tier='T1', status='DONE',
              changed_files=sorted(set(changed)), task_contract_sha256=task_contract_sha256(task),
              tests=receipts, resume_command=None)
for kind in ('report', 'handoff'):
    meta = dict(common, artifact=kind.upper())
    body = (f'本次选定最新正式model{r["checkpoint_iteration"]}已严格加载并完成20秒MP4；路径{r["video"]}。' + review + '\n\n' + summary +
            '\n\n500帧完整解码PASS，关键帧已视觉检查；源代码和checkpoint hash保持，未修改生产配置或操作后台训练。身份及回合数据见docs/carrybox/wall5_play3200_v19_20261020。已有输出不覆盖，重新录制另存目录；无需恢复任务。\n')
    (ROOT / f'agent/{kind}/{slug}.md').write_text('---\n' + '\n'.join(k + ': ' + json.dumps(value, ensure_ascii=False) for k, value in meta.items()) + '\n---\n\n' + body)
validation = validate_paths(*(ROOT / f'agent/{kind}/{slug}.md' for kind in ('plan', 'task', 'report', 'handoff')))
(DOC / 'artifact_validation.json').write_text(json.dumps(validation, indent=2) + '\n')
assert validation['valid'], validation
print(summary)
print(json.dumps(status))
print(json.dumps(validation))
