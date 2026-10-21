"""Publish dated evidence only after formal startup acceptance succeeds."""
from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[3]
DOC=Path(__file__).resolve().parent
slug='carrybox-wall5-headfix-20261021'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256
s=json.loads((DOC/'snapshot.json').read_text()); a=json.loads((DOC/'audit.json').read_text())
smoke=json.loads((DOC/'smoke.json').read_text()); stop=json.loads((DOC/'stopped_run.json').read_text())
receipts=json.loads((DOC/'receipts.json').read_text())['tests']
assert s['status']==smoke['status']=='PASS' and all(t['result']=='PASS' for t in receipts)
text=f'''# wall5 头高标定修正与正式重启（revision20）

{s['checked_at']} 状态快照：实现完成，57项CPU检查、20环境仿真短测和4096环境正式启动验收通过。正式训练进行中，尚未验证拾箱收敛。

已确认本地旧版误用X2头高0.823 m；采用用户校正的head_yaw_link站立中位数1.112 m。G1沿用本地PhysX参考姿态FK的物理head COM 1.21962583 m。仿真复核资产和数据manifest hash与原标定一致。本次未找到X2原始资产，未独立重算X2 FK；1.112的来源保存在checkpoint契约中。

| 参数 | revision19 | revision20 |
|---|---:|---:|
| 头低终止/m | {a['before']['fallen_head']:.6f} | {a['after']['fallen_head']:.6f} |
| 即时成功/站起奖励头高门槛/m | {a['before']['success_head']:.6f} | {a['after']['success_head']:.6f} |
| 站起奖励头高目标/m | {a['before']['stand_head']:.6f} | {a['after']['stand_head']:.6f} |
| 头高指数系数/m⁻¹ | {a['before']['stand_head_exp']:.6f} | {a['after']['stand_head_exp']:.6f} |

头高缩放系数{a['head_scale']:.9f}，使用精确公式而非报告中保留3位的小数。拾箱参考最低头高{a['pickup_reference_min_head_m']:.6f} m，距终止线余量{a['old_head_clearance_m']:.6f}→{a['new_head_clearance_m']:.6f} m。旧目标高于参考中位数，不能据此声称物理上永远不可达。

移除early_failure及其日志索引。旧−50为权重，RewardManager乘policy dt=0.02后是终止转移−1，再进入任务/AMP混合；不是每次直接−50。跌倒/超时/非有限检查仍保留。roll0.5、pitch1.1、骨盆阈值0.231137、3D近箱距离0.783688 m、箱高标定均保持。

终止注册拆为fell_pelvis/fell_head。当前IsaacLab的Episode_Termination只保留每环境最后触发原因；准确的多原因统计使用`Skill/{{loco,pickup,hold}}_fell_pelvis_fraction`、`Skill/{{loco,pickup,hold}}_fell_head_fraction`，分母为该技能已完成回合数，reset前读取物理状态，两者同时触发分别计入但fell合计只计一次。tipped也按reset前真实状态统计，因此多原因比例可相加超过1。

RSI仍75/5/20（3072/205/819）；pickup为0–31贴地帧，hold保持手边参考箱高。actor仍4帧本体+深度，critic独立108维特权MLP；AMP60维/13片段、辅助可见性监督、推扰、深度、碰撞、PD、PPO和足球均未调整。站位距离及膝碰撞未在本轮改变。

验证：57项CPU通过；真实G1四种受控姿态分别产生骨盆低/头低/同时低/均正常，部分reset记录两个原因各2次、fell合计3次。20环境覆盖15 loco/1 pickup/4 hold，PPO/AMP更新2轮、严格保存恢复再更新1轮；新模型恢复前后actor/critic输出完全一致，revision19严格恢复被拒绝。短测模型仅为验证产物。第一次短测断言漏列原有invalid非有限保护，修正测试期望后通过，失败回执保存在attempt1_active_terms中；未删除保护或放宽阈值。

旧PID{stop['pid']}已停止，日志至{stop['last_log_iteration']}轮，保留模型`{stop['last_saved_checkpoint']}`及历史日志；最后未保存迭代未恢复。新PID{s['pid']}，4096环境/seed42/40000轮，从头训练，无resume/checkpoint/warm-start。检查至{s['progress_to']}轮，近10轮平均{s['mean_iteration_seconds']:.3f}s、最慢{s['max_iteration_seconds']:.3f}s。model_0确认schema2/revision20、优化器step20、AMP Normalizer count61440及全部新契约；参数/优化器有限。该验证不代表已学会抱箱。

训练目录：`{s['run']}`

```bash
tail -f {s['log']}
```

[参数审计](audit.json)、[CPU日志](cpu.log)、[仿真短测](smoke.json)、[正式启动验收](snapshot.json)、[冻结测试回执](receipts.json)。
'''
(DOC/'README.md').write_text(text)
summary=f'2026-10-21：[wall5头高修正revision20与从零重启]({{link}})：X2头高锚点按用户更正0.823→1.112 m，G1头低/门控/目标修正为0.438714/0.877429/0.932268 m，移除early_failure并分开统计低骨盆/低头。57项CPU、20环境2＋1轮更新恢复及4096正式启动通过。旧PID{stop["pid"]}已停，新PID{s["pid"]}，RSI75/5/20，检查至{s["progress_to"]}轮，近10轮平均{s["mean_iteration_seconds"]:.3f}s、最慢{s["max_iteration_seconds"]:.3f}s。X2 FK未本地复算；正式训练进行中，尚未证明拾箱收敛。'
for p,link in [(ROOT/'projects/README.md','../docs/carrybox/wall5_headfix_20261021/README.md'),(ROOT/'projects/findbox/README.md','../../docs/carrybox/wall5_headfix_20261021/README.md')]:
 old=p.read_text(); marker='[wall5头高修正revision20与从零重启]'
 if marker not in old:
  title,body=old.split('\n',1);p.write_text(title+'\n\n'+summary.format(link=link)+'\n'+body)
task,_=load_frontmatter(ROOT/f'agent/task/{slug}.md')
changed=set(json.loads((DOC/'before.json').read_text())['source_before'])
changed.update(p.relative_to(ROOT).as_posix() for p in DOC.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
changed.update(['projects/README.md','projects/findbox/README.md',str((DOC/'artifact_validation.json').relative_to(ROOT))])
changed.update(f'agent/{kind}/{slug}.md' for kind in ('plan','task','report','handoff'))
for kind in ('report','handoff'):
 data=dict(task_id=slug,language='zh-CN',axes=['L'],risk_tier='T2',artifact=kind.upper(),status='DONE',changed_files=sorted(changed),tests=receipts,task_contract_sha256=task_contract_sha256(task))
 if kind=='handoff':data['resume_command']=None
 body=text if kind=='report' else f'''实现、短测及正式启动验收已完成；训练PID{s['pid']}仅为{s['checked_at']}快照，下次操作先读/proc、launch.json和snapshot.json。正式run：{s['run']}。\n\n保持revision20、RSI75/5/20、无旧模型恢复。训练继续运行，未做收敛评估。X2头高是用户校正，不能写成本机复算。原因统计用Skill/*_fell_pelvis_fraction及fell_head_fraction；Episode_Termination是manager互斥最后原因。全量说明和命令见docs/carrybox/wall5_headfix_20261021/README.md。旧模型保留；严格restore会拒绝旧环境契约。\n\n只读日志：`tail -f {s['log']}`。不要再次执行launch.py；start_and_verify.sh用launch.json防重复，仅在后续确有验收需要时运行。'''
 (ROOT/f'agent/{kind}/{slug}.md').write_text('---\n'+''.join(f'{k}: {json.dumps(v,ensure_ascii=False)}\n' for k,v in data.items())+'---\n\n'+body+'\n')
print('Project and engineering records updated')
