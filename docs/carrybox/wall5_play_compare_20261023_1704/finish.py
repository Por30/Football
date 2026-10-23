"""Package the checked video; never modify production training."""
from pathlib import Path
import datetime
import hashlib
import json
import sys

D = Path(__file__).resolve().parent
R = D.parents[2]
slug = 'carrybox-wall5-play-compare-20261023-1704'
r = json.loads((D/'recording.json').read_text())
v = json.loads((D/'video_validation.json').read_text())
s = json.loads((D/'selection.json').read_text())
b = json.loads((D/'behavior.json').read_text())
c = json.loads((D/'comparison.json').read_text())
assert c['status'] == 'PASS'
receipts = json.loads((D/'receipts.json').read_text())['tests']
review = (D/'visual_review.txt').read_text().strip()
assert review and r['status'] == v['status'] == 'PASS'
assert all(x['result'] == 'PASS' for x in receipts)
assert hashlib.sha256(Path(r['checkpoint']).read_bytes()).hexdigest() == r['checkpoint_sha256']
for name, digest in s['source_sha256'].items():
    assert hashlib.sha256((R/name).read_bytes()).hexdigest() == digest, name
pid = s['training_pid']
cmd = [x.decode() for x in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if x]
ticks = Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()[19]
assert cmd == s['training_command'] and ticks == s['training_start_ticks']
status = dict(checked_at=datetime.datetime.now().astimezone().isoformat(), pid=pid,
              same_process_running=True, training_process_modified=False,
              source_and_checkpoint_unchanged=True)
(D/'formal_status.json').write_text(json.dumps(status, indent=2)+'\n')
video = Path(r['video'])
O = video.parent
summary = (f'rev27 model_{r["checkpoint_iteration"]}，4机器人同步20秒，1080p/25fps、高位镜头。'
           f'固定来源为默认/loco/loco/hold，reset次数{r["reset_counts"]}；保留完整回合；与model2800使用相同初态及2200轮课程。')
table = ['| 起点 | 完整回合数 | 平均完整回合秒数 | 成功回合 |', '|---|---:|---:|---:|']
for name, g in b['groups'].items():
    seconds = f'{g["mean_completed_seconds"]:.3f}' if g['mean_completed_seconds'] is not None else '—'
    table.append(f'| {name} | {g["completed_episodes"]} | {seconds} | {g["completed_successes"]} |')
text = f'''# Wall5 rev27 model{r['checkpoint_iteration']} 回放

[观看20秒MP4](../../../outputs/carrybox/{O.name}/{video.name}) · [关键帧拼图](../../../outputs/carrybox/{O.name}/contact_sheet.jpg)

{summary}

{review}

{chr(10).join(table)}

选取时间：{s['selected_at']}。当时最新完整checkpoint：`{r['checkpoint']}`。录像固定该模型，不追换录制期间新保存的模型。

保持rev27默认固定来源配额；4环境离散分配为1默认、2loco、1hold，本段没有pickup来源。每次reset仍重新随机参考帧/状态；hold起点已有箱子，不能算从地面抓起。完整回合统计不包含结尾尚未结束的回合，终止原因可以重叠。单seed、4环境仅用于观察，不是总体成功率评估。

seed42、均值动作，严格加载完整环境契约和策略权重。为比较权重进步，回放课程固定为第2200轮：yaw {r['yaw_degrees']:.2f}°、推扰强度{r['push_scale']:.2f}，与旧model2800相同。录像没有使用当前正式训练轮数对应的更强推扰；这项诊断覆盖已记录，正式训练不受影响。保留原障碍、自碰撞、随机化和动作延迟；50Hz策略、200Hz物理、500帧。四台旁观相机同步渲染，基准高度5.8m；每格深度角标来自actor实际米制深度，除3仅用于灰度显示。逐帧检查旁观渲染不推进物理、不改机器人状态，策略权重与checkpoint哈希不变。

视频完整解码通过，{v['file_bytes']/1024/1024:.2f}MiB。已检查关键帧和行为轨迹。正式训练PID{pid}于{status['checked_at']}仍为同一进程；本次没有停止、重启或修改训练。

[新旧对比数据](comparison.json)、[对比图](../../../outputs/carrybox/{O.name}/comparison.png)、[初态核验](initial_match.json)、[配置与回合](recording.json)、[行为统计](behavior.json)、[轨迹](trajectory.json)、[完整解码校验](video_validation.json)、[执行回执](receipts.json)。后续录像新建目录，保留当前产物。
'''
(D/'README.md').write_text(text)
(O/'README.md').write_text(f'# Wall5 model{r["checkpoint_iteration"]} play\n\n[观看20秒MP4]({video.name}) · [关键帧拼图](contact_sheet.jpg)\n\n'+summary+'\n\n'+review+f'\n\n[完整记录](../../../docs/carrybox/{D.name}/README.md)。\n')
for name, prefix in [('projects/README.md', '../'), ('projects/findbox/README.md', '../../')]:
    p = R/name
    title, body = p.read_text().split('\n', 1)
    link = prefix+f'docs/carrybox/{D.name}/README.md'
    assert link not in body
    p.write_text(title+f'\n\n2026-10-23：[rev27 model{r["checkpoint_iteration"]}四机器人录像]({link})：'+summary+' 正式训练继续；同初态同课程对比model2800，具体抖动/抓取表现见录像记录；未作总体成功率评估。\n'+body)
sys.path.insert(0, '/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter, task_contract_sha256, validate_paths
task, _ = load_frontmatter(R/f'agent/task/{slug}.md')
changed = [str(p.relative_to(R)) for folder in (D, O) for p in folder.rglob('*')
           if p.is_file() and '__pycache__' not in p.parts]
changed += [str(D.relative_to(R)/'artifact_validation.json'), 'projects/README.md', 'projects/findbox/README.md']
changed += [f'agent/{k}/{slug}.md' for k in ('plan', 'task', 'report', 'handoff')]
meta = dict(task_id=slug, language='zh-CN', axes=['L'], risk_tier='T1', status='DONE',
            changed_files=sorted(set(changed)), task_contract_sha256=task_contract_sha256(task),
            tests=receipts, resume_command=None)
for kind in ('report', 'handoff'):
    fields = {**meta, 'artifact': kind.upper()}
    (R/f'agent/{kind}/{slug}.md').write_text('---\n'+'\n'.join(k+': '+json.dumps(val, ensure_ascii=False) for k, val in fields.items())+'\n---\n\n'+summary+'\n\n'+review+'\n\n视频：'+str(video)+'。严格加载、完整解码及关键帧检查通过；正式训练和生产源码保持。没有待恢复工作，后续录像新建目录。\n')
validation = validate_paths(*(R/f'agent/{k}/{slug}.md' for k in ('plan', 'task', 'report', 'handoff')))
(D/'artifact_validation.json').write_text(json.dumps(validation, indent=2)+'\n')
assert validation['valid'], validation
print(summary)
print('ARTIFACTS_VALID; FORMAL_PROCESS_UNCHANGED')
