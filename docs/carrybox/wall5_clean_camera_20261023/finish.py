"""Package revision28 validation and the observed formal-start state."""
from pathlib import Path
from datetime import datetime
import hashlib,json,sys
D=Path(__file__).resolve().parent;R=D.parents[2];slug='carrybox-wall5-clean-camera-20261023'
launch=json.loads((D/'launch.json').read_text());snapshot=json.loads((D/'snapshot.json').read_text())
smoke=json.loads((D/'smoke.json').read_text());stopped=json.loads((D/'stopped_run.json').read_text())
receipts=json.loads((D/'receipts.json').read_text())['tests'];assert all(x['result']=='PASS' for x in receipts)
assert snapshot['status']==smoke['status']=='PASS' and stopped['status']=='exited'
assert snapshot['revision']==28 and snapshot['initialization']=='fresh'
assert [a.decode() for a in Path(f'/proc/{launch["pid"]}/cmdline').read_bytes().split(b'\0') if a]==launch['command']
for name,digest in launch['source_sha256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
summary=(f'wall5 revision28关闭人工相机噪声、丢失、随机延迟/冻结和安装误差；推扰5000轮无扰动，随后10000轮增量爬升。'
         f'15项CPU及64环境2＋1轮PPO/AMP、深度逐像素/标签/安装位姿、课程边界和严格恢复通过。'
         f'旧PID{stopped["pid"]}已停止，新PID{launch["pid"]}，4096环境从零启动，检查至{snapshot["iteration"]}轮，'
         f'近10轮平均{snapshot["mean_iteration_seconds"]:.3f}秒、最慢{snapshot["max_iteration_seconds"]:.3f}秒。'
         '正式训练进行中，未验证抖动改善或抓取收敛。')
details=f'''# Wall5 revision28：干净深度与早期低推扰

{summary}

| 配置 | revision27 | revision28 |
|---|---|---|
| 高斯深度噪声 | 0.02m | 0 |
| 距离相关深度噪声 | 0.008–0.03m | 0 |
| 边缘丢失 / 随机孔洞 | 5% / 2% | 0 / 0 |
| 深度随机延迟 | 10%概率延迟1步 | 0，单槽缓存 |
| 短时冻结 | 0.2%概率，最长15帧 | 0 |
| 相机安装位置 / 角度误差 | 0.01m / 0° | 0 / 0 |
| 推扰开始 / 爬升时长 | 1000 / 4000轮 | 5000 / 10000轮 |

推扰强度按有效训练迭代clamp((iter−anchor−5000)/10000,0,1)：0–5000轮为0，10000轮为0.5，15000轮后为1。保持当前COM世界速度加随机增量，原1–3秒事件间隔和最终幅度不变。课程仍以当前进程首次真实iteration为锚点，恢复新进程时沿用原有重新锚定行为。

真实G1相机名义安装、光轴米制0.1–3m、48×27、50Hz、4帧、机器人自身/障碍/地面遮挡保持。actor深度＋本体、critic123、辅助监督、AMP完整15段、RSI固定配额、自碰撞、PD、物理动作延迟0–20ms、奖励和终止保持。本次“减少早期扰动”具体指推迟和放缓外部速度推扰；其他物理随机化保持。

只修改wall5配置与其checkpoint revision；共享深度/AMP/PPO及football、wall3/wall4源码未变。schema仍为2，revision28可严格恢复；rev27完整恢复被拒绝。正式训练未加载旧权重、优化器或Normalizer。

实际仿真中{smoke['depth_checks']}次捕获检查：actor最新深度与Warp原始光轴深度经既有缺失处理/裁剪后逐元素一致，标签来自当前帧，安装外参无随机误差。单槽连续/重复/partial reset、非零锚点的推扰0/0.5/1和无写入边界通过。两轮更新＋恢复后一轮，策略/CNN/辅助头/critic和AMP优化器均更新且有限；actor/critic恢复输出一致。失败首次测试保存在attempt1_mount_reference，原因是测试基准未包含名义相机坐标转换链；修正参考后保持原容差及生产实现，没有放宽断言。

验证模型仅在本docs目录，不能作为正式训练或任务成功证据。正式首model_0核验全新优化器20步、AMP Normalizer计数61440、配置与已验证契约一致。检查时间：{snapshot['checked_at']}，当前快照不是训练完成或收敛结论。

- 正式run：`{snapshot['run']}`
- 日志：`{snapshot['log']}`
- PID：`{launch['pid']}`
- 旧run保留：`{stopped['old_run']}`
- 旧进程最后保存：`{stopped['last_saved_checkpoint']}`

查看日志：

```bash
tail -f '{snapshot['log']}'
```

正式启动参数（已在运行，无需重复执行）：

```bash
{' '.join(launch['command'])}
```

[本轮源码差异](source_changes.patch) · [范围核验](scope_check.json) · [仿真检查](smoke.json) · [正式快照](snapshot.json) · [启动记录](launch.json) · [旧训练退出记录](stopped_run.json) · [测试回执](receipts.json)
'''
(D/'README.md').write_text(details)
for name,prefix in [('projects/README.md','../'),('projects/findbox/README.md','../../')]:
    p=R/name;title,body=p.read_text().split('\n',1);link=prefix+'docs/carrybox/wall5_clean_camera_20261023/README.md'
    assert link not in body
    p.write_text(title+f'\n\n2026-10-23：[wall5关闭相机噪声并减缓推扰重启]({link})：'+summary+'\n'+body)
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
task,_=load_frontmatter(R/f'agent/task/{slug}.md')
changed=[str(p.relative_to(R)) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
changed+=json.loads((D/'scope_check.json').read_text())['production_changed']
changed+=['projects/README.md','projects/findbox/README.md',str(D.relative_to(R)/'artifact_validation.json')]
changed+=[f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')]
changed+=[str(p.relative_to(R)) for p in Path(snapshot['run']).rglob('*') if p.is_file()]
changed+=[str(Path(snapshot['log']).relative_to(R))]
meta=dict(task_id=slug,language='zh-CN',axes=['P','L'],risk_tier='T2',status='DONE',changed_files=sorted(set(changed)),
          task_contract_sha256=task_contract_sha256(task),tests=receipts,resume_command=None)
body=summary+'\n\n相机真实遮挡、米制和全部训练接口保持；详见 '+str(D/'README.md')+'。\n\n查看正式日志：`tail -f '+snapshot['log']+'`。本工程工作已完成，正式训练仍进行中，未评估长训效果。\n'
for kind in ('report','handoff'):
    fields={**meta,'artifact':kind.upper()}
    (R/f'agent/{kind}/{slug}.md').write_text('---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in fields.items())+'\n---\n\n'+body)
result=validate_paths(*(R/f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')))
(D/'artifact_validation.json').write_text(json.dumps(result,indent=2)+'\n');assert result['valid'],result
print(summary);print('ARTIFACTS_VALID')
