"""Publish startup evidence after the frozen acceptance command passes."""
from pathlib import Path
import json, sys

DOC=Path(__file__).resolve().parent
ROOT=DOC.parents[2]
SLUG='carrybox-wall5-rsi5-fresh-20261021'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter, task_contract_sha256, validate_paths

s=json.loads((DOC/'snapshot.json').read_text())
l=json.loads((DOC/'launch.json').read_text())
old=json.loads((DOC/'stopped_run.json').read_text())
receipts=json.loads((DOC/'receipts.json').read_text())['tests']
assert s['status']=='PASS' and all(t['result']=='PASS' for t in receipts)
assert old['status']=='exited' and s['initialization']=='fresh' and s['rsi']==[.75,.05,.2]
cmd=[a.decode() for a in Path(f'/proc/{s["pid"]}/cmdline').read_bytes().split(b'\0') if a]
assert cmd==l['command']
summary=(f'旧PID{old["pid"]}已停止，最后日志迭代{old["last_log_iteration"]}、'
         f'{Path(old["last_saved_checkpoint"]).name}及全部历史日志保留。'
         f'新wall5以RSI75/5/20、4096环境、seed42、40000轮从零启动，PID{s["pid"]}；'
         f'检查至{s["progress_to"]}轮，近10轮平均{s["mean_iteration_seconds"]:.3f}s、最慢{s["max_iteration_seconds"]:.3f}s。'
         '首模型确认新RSI、schema2/revision19、全新优化器/Normalizer；正式训练进行中，尚未验证抱起成功。')
body=f'''# Wall5 新RSI75/5/20从零正式训练

{summary}

启动核验时间：{s['checked_at']}。用户明确要求停止当前训练并重新启动新训练；本次按已说明的fresh方式执行，无resume、warm-start或checkpoint输入。其他revision19训练配方保持，未额外修改拾取奖励。

原进程完整命令与start_ticks核对后发送SIGINT，确认退出和显存释放再启动新进程。旧日志与模型均保留；最后落盘模型之后的训练尾部没有保存成新checkpoint。新启动前可用显存{l['free_mib_before']}MiB，13段ground_pickup数据hash全部核对。

新RSI固定配额为3072 loco、205 pickup、819 hold。pickup仅第0–31帧，箱底5mm、无平台；hold保持手边参考箱高。AMP专家仍40/40/20、60维特征，actor深度＋本体，critic独立108维MLP，roll阈值0.5。完整模型契约与已通过的20环境reset验收一致；新日志实际transition比例也已核对为3072/4096、205/4096、819/4096。

首个model_0.pt中PPO与AMP优化器step均为20，AMP Normalizer count=61440，参数/优化器均有限；配置resume=false，说明新进程从零开始。已观察至少16个完整迭代，并检查近10轮均小于6秒。生产源码hash未变化，快照在source_snapshot/。

首次启动验收的完整契约比较遇到存储格式差异：torch checkpoint保留随机化范围的tuple，短测JSON将其转换成list。统一为JSON表示后，完整契约所有字段一致；检查范围与断言数值保持。失败回执保留在attempt1_contract_format/，仅重跑只读验收，没有再次启动、停止或修改训练。

正式run：`{s['run']}`

首个checkpoint：`{s['checkpoint']}`

查看日志：

```bash
tail -n 100 -f "{s['log']}"
```

查看进程：

```bash
ps -p {s['pid']} -o pid,etime,args
```

只读复查：

```bash
cd /home/cao/perceptual_ball
/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_rsi5_fresh_20261021/verify.py
```

[停止记录](stopped_run.json) · [启动记录](launch.json) · [启动核验](snapshot.json) · [回执](receipts.json)。launch.json用于防重复启动；后续操作前重新核对进程。本次完成启动，不代表40000轮结束或已学会搬箱。
'''
(DOC/'README.md').write_text(body)
for name,prefix in [('projects/README.md','../'),('projects/findbox/README.md','../../')]:
    p=ROOT/name
    title,rest=p.read_text().split('\n',1)
    link=prefix+'docs/carrybox/wall5_rsi5_fresh_20261021/README.md'
    assert link not in rest
    p.write_text(title+'\n\n2026-10-21：[wall5 RSI75/5/20正式从零重启]('+link+')：'+summary+'\n'+rest)
p=ROOT/'projects/findbox/README.md'
text=p.read_text()
old_row='当前默认RSI为75%loco/5%pickup/20%hold（2026-10-21调整，运行中旧进程仍80/0/20）'
assert old_row in text
p.write_text(text.replace(old_row,'当前正式RSI为75%loco/5%pickup/20%hold（2026-10-21从零启动）'))
task,_=load_frontmatter(ROOT/f'agent/task/{SLUG}.md')
changed=[str(p.relative_to(ROOT)) for p in DOC.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
changed+=[str(p.relative_to(ROOT)) for p in Path(s['run']).rglob('*') if p.is_file()]
changed += ['projects/README.md','projects/findbox/README.md',str(Path(s['log']).relative_to(ROOT)),
            str(Path(old['old_log']).relative_to(ROOT)),str((DOC/'artifact_validation.json').relative_to(ROOT))]
changed += [f'agent/{kind}/{SLUG}.md' for kind in ('plan','task','report','handoff')]
for kind in ('report','handoff'):
    meta=dict(task_id=SLUG,language='zh-CN',axes=['L'],risk_tier='T2',artifact=kind.upper(),status='DONE',
        changed_files=sorted(set(changed)),task_contract_sha256=task_contract_sha256(task),tests=receipts,resume_command=None)
    content=summary+'\n\n本任务完成停止旧训练、从零启动新训练和启动验收。不是完成40000轮或成功率评估。'
    content+='\n\n新日志：'+s['log']+'\n\n新run：'+s['run']
    content+='\n\n详情：docs/carrybox/wall5_rsi5_fresh_20261021/README.md。不要重复启动；后续先核对实际PID和命令。生产代码、其他任务、AMP数据保持。'
    (ROOT/f'agent/{kind}/{SLUG}.md').write_text('---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in meta.items())+'\n---\n\n'+content+'\n')
v=validate_paths(*(ROOT/f'agent/{kind}/{SLUG}.md' for kind in ('plan','task','report','handoff')))
(DOC/'artifact_validation.json').write_text(json.dumps(v,indent=2)+'\n')
assert v['valid'],v
print(summary)
print(v)
