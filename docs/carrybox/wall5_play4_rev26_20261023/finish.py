from pathlib import Path
import json, hashlib, datetime, sys

D = Path(__file__).resolve().parent
R = D.parents[2]
O = R/'outputs/carrybox/wall5_play4_rev26_20261023'
slug = 'carrybox-wall5-play4-rev26-20261023'
r = json.loads((D/'recording.json').read_text())
v = json.loads((D/'video_validation.json').read_text())
s = json.loads((D/'selection.json').read_text())
b = json.loads((D/'behavior.json').read_text())
receipts = json.loads((D/'receipts.json').read_text())['tests']
review = (D/'visual_review.txt').read_text().strip()
assert review and r['status']==v['status']=='PASS' and all(x['result']=='PASS' for x in receipts)
assert hashlib.sha256(Path(r['checkpoint']).read_bytes()).hexdigest()==r['checkpoint_sha256']
for name,h in s['source_sha256'].items():
    assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h, name
pid=s['training_pid']
cmd=[x.decode() for x in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if x]
ticks=Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()[19]
assert cmd==s['training_command'] and ticks==s['training_start_ticks']
status=dict(checked_at=datetime.datetime.now().astimezone().isoformat(),pid=pid,
    same_process_running=True,training_process_modified=False,source_and_checkpoint_unchanged=True)
(D/'formal_status.json').write_text(json.dumps(status,indent=2)+'\n')
labels=['默认站姿','loco RSI','pickup RSI','hold RSI']
table=['| 画面 | 初始起点 | 20秒内reset次数 |','|---|---|---:|']
for i in range(4):table.append(f'| {i+1} | {labels[r["initial_kinds"][i]]} | {r["reset_counts"][i]} |')
summary=(f'最新完整model_{r["checkpoint_iteration"]}.pt，revision26，4环境同步20秒、1920×1080/25fps、高位镜头基准5.8m。'
         f'默认随机reset保持，每格reset次数{r["reset_counts"]}；起点标签随回合变化，失败过程完整保留。')
video=Path(r['video']).name
text=f'''# Wall5 rev26 最新checkpoint四机器人回放

[观看20秒MP4](../../../outputs/carrybox/wall5_play4_rev26_20261023/{video}) · [关键帧拼图](../../../outputs/carrybox/wall5_play4_rev26_20261023/contact_sheet.jpg)

{summary}

选取时间：{s['selected_at']}。Checkpoint：`{r['checkpoint']}`。录制期间正式训练继续，视频固定使用该模型，不追换后续保存的模型。

{review}

{chr(10).join(table)}

本版按原始20%默认站姿＋80%随机RSI初始化，**不再是旧版固定3loco+1hold**。每次reset仍按默认随机抽样，不筛选起点。DEFAULT/LOCO为地面箱起点；PICKUP可能从动作中途开始，HOLD从持箱参考开始。这两类不能直接计作地面拾箱成功。终止原因从实际TerminationManager读取，可能重叠，不能把各原因相加作为回合总数。

4环境在同一play进程同步50Hz推理/200Hz物理，四台旁观相机每两步渲染一次，组成500帧20秒四宫格。镜头沿用上一段高位设置，视线跟随机器人与箱子中点；逐帧确认旁观渲染不推进物理时间、不改变机器人状态。每格角标为actor实际米制深度的灰度显示，除3仅用于显示。

严格核对完整环境契约及模型权重，恢复第{r['checkpoint_iteration']}轮yaw课程{r['yaw_degrees']:.2f}°和推扰强度{r['push_scale']:.2f}。seed42、均值动作；保持真实任务障碍物、自碰撞、reset、噪声和动作延迟。没有训练/优化器更新。视频完整解码通过，{v['file_bytes']/1024/1024:.2f}MiB；已人工检查关键帧。本段仅为4环境单seed观察，不作为总体成功率评估。

后台PID{pid}在{status['checked_at']}仍为原进程；没有停止、重启或调参。源码hash、checkpoint hash和策略权重保持。

[录像配置和回合](recording.json)、[分起点表现统计](behavior.json)、[轨迹](trajectory.json)、[视频校验](video_validation.json)、[执行回执](receipts.json)。现有输出不覆盖；再次录制应新建目录。
'''
(D/'README.md').write_text(text)
(O/'README.md').write_text(f'# Wall5 model{r["checkpoint_iteration"]} play\n\n[观看20秒MP4]({video}) · [关键帧拼图](contact_sheet.jpg)\n\n'+summary+'\n\n'+review+'\n\n[完整记录](../../../docs/carrybox/wall5_play4_rev26_20261023/README.md)。\n')
for name,prefix in [('projects/README.md','../'),('projects/findbox/README.md','../../')]:
    p=R/name;title,body=p.read_text().split('\n',1)
    link=prefix+'docs/carrybox/wall5_play4_rev26_20261023/README.md'
    assert link not in body
    p.write_text(title+'\n\n2026-10-23：[wall5最新model13200四机器人录像]('+link+')：'+summary+review+' 正式训练继续，未作总体成功率评估。\n'+body)
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
task,_=load_frontmatter(R/f'agent/task/{slug}.md')
changed=[str(p.relative_to(R)) for folder in (D,O) for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
changed += [str(D.relative_to(R)/'artifact_validation.json'),'projects/README.md','projects/findbox/README.md']
changed += [f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')]
meta=dict(task_id=slug,language='zh-CN',axes=['L'],risk_tier='T1',status='DONE',
    changed_files=sorted(set(changed)),task_contract_sha256=task_contract_sha256(task),tests=receipts,resume_command=None)
for kind in ('report','handoff'):
    fields={**meta,'artifact':kind.upper()}
    (R/f'agent/{kind}/{slug}.md').write_text('---\n'+'\n'.join(k+': '+json.dumps(val,ensure_ascii=False) for k,val in fields.items())+'\n---\n\n'+summary+'\n\n'+review+'\n\n视频：'+r['video']+'。严格加载、完整解码、关键帧检查通过；不改生产或正式训练。当前起点随机，不能套用旧版固定3loco+1hold描述。没有待恢复工作；既有产物不覆盖。\n')
validation=validate_paths(*(R/f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')))
(D/'artifact_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
assert validation['valid'],validation
print(summary)
print('ARTIFACTS_VALID; FORMAL_PROCESS_UNCHANGED')
