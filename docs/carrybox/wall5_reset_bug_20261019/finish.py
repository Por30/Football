"""Publish only completed checks and the observed formal-run state."""
from pathlib import Path
import json, sys, statistics, hashlib
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2]
SLUG='carrybox-wall5-reset-bug-20261019'
s=json.loads((DOC/'snapshot.json').read_text());launch=json.loads((DOC/'launch.json').read_text())
receipts=json.loads((DOC/'receipts.json').read_text())['tests']
pilot=json.loads((DOC/'pilot.json').read_text());old=json.loads((DOC/'attempt1/pilot.json').read_text())
assert s['status']=='PASS' and pilot['status']=='PASS' and all(r['result']=='PASS' for r in receipts)
assert pilot['contract']['reward_weights']['locomotion_stability']==5.
assert old['contract']['reward_weights']['locomotion_stability']==2.
comparison={}
for label,data in [('weight2',old),('weight5',pilot)]:
 comparison[label]={}
 for period in ['first_25','last_25']:
  v=data[period];metrics=v['metrics']
  comparison[label][period]=dict(loco=v['loco'],hold=v['hold'],seconds=v['seconds_per_iteration'],
    loco_task_per_step=metrics['Reward/loco_task_per_step'],
    loco_task_excluding_failure=metrics['Reward/loco_task_per_step']-metrics['Reward/loco_early_failure_per_step'],
    saturation=metrics['Control/physical_target_clipped_fraction'],
    surviving_loco_speed=metrics['Motion/loco_survivor_speed_mps'],surviving_loco_box_distance=metrics['Motion/loco_survivor_box_distance_m'])
(DOC/'pilot_comparison.json').write_text(json.dumps(comparison,indent=2))
summary=(f"wall5 revision17训练反馈修复已完成工程检查并从零启动4096环境正式run，PID{s['pid']}；"
 f"检查至{s['progress_to']}轮，最近10轮平均{s['mean_iteration_seconds']:.3f}秒、最慢{s['max_iteration_seconds']:.3f}秒。"
 "旧6600回放确认空手约0.27秒倾倒，采样噪声膨胀、缺少空手平衡反馈和实际采样偏向hold构成明确训练缺口；未发现GAE跨回合泄漏。"
 "新增平衡反馈及walk姿态门控、std≤1/动作均值界正则、固定80/20环境配额；PD、roll0.5、深度和13段AMP保持。"
 "39项CPU、4环境PPO/AMP 2＋1轮恢复导出、512环境200轮fresh检查通过。正式训练进行中，长期站走/拾箱能力尚未验证。")
a,b=pilot['first_25']['loco'],pilot['last_25']['loco']
runtime=f'''\n## 最终工程验收与正式运行快照

{s['checked_at']}：{summary}

新反馈权重5的512×200轮pilot，首25轮loco已完成回合均长{a['mean_steps']:.2f}步，末25轮{b['mean_steps']:.2f}步；末窗口tipped比例{b['tipped']:.3%}。这是一段训练采样统计，不是独立站走成功率，不能据此认定会走路。权重2与5的同seed对比见[pilot_comparison.json](pilot_comparison.json)。首版反馈权重2的CPU失败fixture及其仿真通过结果全部保存在attempt1；原测试断言未放宽。

正式目录：`{s['run']}`，seed42、40000轮，从零初始化，未加载旧模型或docs短训模型。首model_0确认revision17、actor500输入/critic108、AMP13段60维、优化器step20、Normalizer count61440、固定3277loco/819hold配额与std≤1。原始PID退出原因未从日志确定，本次没有向不存在的旧进程发送信号。

查看训练：

```bash
tail -f '{s['log']}'
```

实际启动参数（已在运行，无需重复启动）：

```bash
{' '.join(launch['command'])}
```

运行环境设置与去重/资源检查见launch.sh/launch.py。源码快照和SHA、数据manifest身份见launch.json；正式启动检查见snapshot.json。时间、PID、迭代均为带时间快照，下次操作需重新核对真实进程。
'''
p=DOC/'README.md';p.write_text(p.read_text()+runtime)
entry=(f"2026-10-19：[wall5 revision17空手倾倒修复与重启]({{link}})：旧6600均值/采样各32回合全部约0.27秒倾倒；"
 "新增平衡反馈、walk姿态门控、std≤1/动作均值界正则和固定80/20环境配额，原PD/roll0.5/深度/AMP保持。"
 f"39项CPU、4环境更新恢复导出及512×200短训通过；正式4096 fresh PID{s['pid']}，检查{s['progress_to']}轮、平均{s['mean_iteration_seconds']:.3f}秒/轮。"
 "训练进行中，尚未验证稳定行走/地面拾箱。\n\n")
for name,prefix in [('projects/README.md','../'),('projects/findbox/README.md','../../')]:
 p=ROOT/name;text=p.read_text();assert 'wall5_reset_bug_20261019/README.md' not in text
 title,rest=text.split('\n\n',1);p.write_text(title+'\n\n'+entry.format(link=prefix+'docs/carrybox/wall5_reset_bug_20261019/README.md')+rest)
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256
frozen,_=load_frontmatter(ROOT/f'agent/task/{SLUG}.md')
changed=list(json.loads((DOC/'before_hashes.json').read_text()))+['tests/test_carrybox_reset_bug.py','projects/README.md','projects/findbox/README.md']
changed += [str(p.relative_to(ROOT)) for p in DOC.iterdir() if p.is_file() and p.suffix in ('.py','.sh','.md','.json')]
changed += [f'agent/{kind}/{SLUG}.md' for kind in ['plan','task','report','handoff']]
meta=dict(task_id=SLUG,language='zh-CN',axes=['E','C','L'],risk_tier='T2',status='DONE',changed_files=sorted(changed),task_contract_sha256=task_contract_sha256(frozen),tests=receipts,resume_command=None)
for kind in ['report','handoff']:
 m=dict(meta,artifact=kind.upper())
 body=summary+'\n\n'+f"完整设计/证据：docs/carrybox/wall5_reset_bug_20261019/README.md。正式run：{s['run']}；日志：{s['log']}。\n\n"
 body+='本次完成工程修复、排查和正式启动；没有完成40000轮或证明会走路/搬箱。必须看新checkpoint的loco独立回放，不能以hold存活或总体回合长度代替成功。固定配额改变reset概率语义，源码/环境契约已升级；旧模型不可严格resume。未改共享资产/足球接口/数据，工作区旧改动和历史失败产物保留。\n\n'
 body+='首批CPU失败是fixture未指定fixed schedule，随后修复fixture及显式warm-start上限边界，并仅将平衡奖励2→5按相同pilot对比；保留attempt1和repair1，原断言未放宽。下一操作前只读核对launch.json的实际PID命令，不重复启动。\n'
 (ROOT/f'agent/{kind}/{SLUG}.md').write_text('---\n'+''.join(k+': '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in m.items())+'---\n\n'+body)
print(summary)
