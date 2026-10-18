from pathlib import Path
import json,sys
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];slug='carrybox-wall5-fresh-20261018'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
receipts=json.loads((OUT/'receipts.json').read_text())['tests'];assert all(r['result']=='PASS' for r in receipts)
s=json.loads((OUT/'snapshot.json').read_text());assert s['initialization']=='fresh' and s['loaded_checkpoint'] is None
body=f'''# Wall5从零正式启动（2026-10-18）

按用户“不用恢复，重新启动”的明确要求，已停止恢复运行PID3810947，保留旧run/checkpoint/log；从零启动当前优化版wall5。

- PID：{s['pid']}；4096环境、seed42、40000轮。
- 初始化：fresh，命令无resume/checkpoint/warm-start；实际agent.yaml为resume:false，日志无checkpoint加载记录。
- 首model_0.pt：PPO与AMP优化器step均20（首次5epochs×4minibatches更新），Normalizer running_count=61440（专家初始化20480＋首更新40960）；确认不是继承旧优化器/Normalizer。
- 契约：schema2 / environment revision13 / AMP config3，13段ground_pickup数据、60D AMP，RSI80%loco/0%pickup/20%hold。深度、自遮挡、全身碰撞和性能优化保持，生产源码/配置/数据未改。
- 正式进度快照：{s['checked_at']}，迭代{s['progress_from']}→{s['progress_to']}；最近10轮平均{s['mean_iteration_seconds']:.3f}s、最慢{s['max_iteration_seconds']:.3f}s。参数、PPO/AMP优化器有限值检查通过。训练进行中，未完成长训或证明收敛。
- Run：`{s['run']}`

查看日志：

```bash
tail -f '{s['log']}'
```

launch.json保存实际命令/PID，stopped_run.json保存被替换运行，snapshot.json与receipts.json保存实际检查结果。时间/PID/迭代为快照，下次操作前需实时核对。此前性能与等价性验证沿用../wall5_perf_20261018/，本次只切换fresh启动，不重复额外GPU验证。
'''
(OUT/'README.md').write_text(body)
short=f"{s['checked_at'][:16].replace('T',' ')} JST：[wall5改为从零正式训练]({{link}})：按用户明确要求停止恢复运行PID3810947，新PID{s['pid']}，4096环境、40000轮、fresh，无resume/warm-start。首checkpoint优化器step20与Normalizer count61440确认全新初始化；检查迭代{s['progress_from']}→{s['progress_to']}，最近10轮平均{s['mean_iteration_seconds']:.3f}秒、最慢{s['max_iteration_seconds']:.3f}秒。保留性能优化/revision13/RSI80-0-20；旧产物保留，训练进行中，未证明收敛。"
for file,link in [('projects/README.md','../docs/carrybox/wall5_fresh_20261018/README.md'),('projects/findbox/README.md','../../docs/carrybox/wall5_fresh_20261018/README.md')]:
 p=ROOT/file;heading,rest=p.read_text().split('\n',1);p.write_text(heading+'\n\n'+short.format(link=link)+'\n'+rest)
task,_=load_frontmatter(ROOT/f'agent/task/{slug}.md')
changed=['projects/README.md','projects/findbox/README.md']+[f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')]
changed+= [str(p.relative_to(ROOT)) for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
changed+=[str((OUT/'artifact_validation.json').relative_to(ROOT))];changed=sorted(set(changed))
common={k:task[k] for k in ('task_id','language','axes','risk_tier')};common.update(status='DONE',changed_files=changed,task_contract_sha256=task_contract_sha256(task),tests=receipts)
for kind in ('report','handoff'):
 meta=dict(common,artifact=kind.upper())
 if kind=='handoff':meta['resume_command']=None
 text=body if kind=='report' else f"用户最新要求已落实：仅fresh启动，无checkpoint恢复。PID{s['pid']}，核验{s['checked_at']}至{s['progress_to']}轮，平均{s['mean_iteration_seconds']:.3f}s。日志`{s['log']}`。原恢复进程3810947已停止，所有旧产物保留；当前训练正在进行，尚无收敛结论。详见docs/carrybox/wall5_fresh_20261018/README.md，后续先核对实际进程。当前任务无待办。"
 (ROOT/f'agent/{kind}/{slug}.md').write_text('---\n'+''.join(f'{k}: {json.dumps(v,ensure_ascii=False)}\n' for k,v in meta.items())+'---\n\n'+text+'\n')
result=validate_paths(*(ROOT/f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')))
(OUT/'artifact_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));assert result['valid'],result
print(json.dumps(dict(validation=result,pid=s['pid'],iteration=s['progress_to'],mean=s['mean_iteration_seconds'],maximum=s['max_iteration_seconds'],log=s['log']),ensure_ascii=False,indent=2))
