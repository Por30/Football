"""Record implementation and formal-start acceptance; no convergence claim."""
from pathlib import Path
import json, re, sys
ROOT=Path(__file__).resolve().parents[3]; DOC=Path(__file__).resolve().parent
slug='carrybox-wall5-critic123-aux-20261021'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter, task_contract_sha256
s=json.loads((DOC/'snapshot.json').read_text()); smoke=json.loads((DOC/'smoke.json').read_text())
stop=json.loads((DOC/'stopped_run.json').read_text()); receipts=json.loads((DOC/'receipts.json').read_text())['tests']
assert s['status']==smoke['status']=='PASS' and all(t['result']=='PASS' for t in receipts)
count=int(re.search(r'Ran (\d+) tests', (DOC/'cpu.log').read_text())[1])
body=f'''# wall5 critic123与全帧辅助监督（revision22）

{s['checked_at']}状态快照：实现、{count}项CPU测试、20环境PPO/AMP更新/恢复/导出及4096环境正式启动验收通过。正式训练仍在运行，未评估本版本稳定行走或地面拾箱成功率。

按用户补充明确要求，revision21保留的两项差异本次均改动：

| 项目 | revision21 | revision22 |
|---|---|---|
| critic输入 | 108维 | 123维，新增5个末端位置共15维 |
| 位姿辅助系数 | 0.1 | 1.0 |
| 辅助监督样本 | 深度内可见的配对帧 | 全部配对帧，包括遮挡、超量程、相机后方 |

critic输入依次为本体93、骨盆link线速度3、箱子相对位置3、相对旋转6、箱体尺寸3、新增末端位置15。前108维顺序保持，末端追加在108:123；rot6仍是骨盆逆旋转乘箱体旋转的前两列，旋转重建测试通过。新增15维按left_palm_link、right_palm_link、left_ankle_pitch_link、right_ankle_pitch_link、mid360_link排序，取实际G1连杆原点到骨盆link原点的偏移、逆旋转至骨盆坐标系，单位米；没有取COM、碰撞面中心或X2腰关节。与现有G1 AMP五端点命名一致，真实PhysX读回与观测转换核对通过。

critic使用独立512/256/256 MLP，含新增末端的终止前状态用于timeout bootstrap。actor保持93×4=372维本体和4×27×48米制深度，CNN输出128维后拼接MLP；critic真值不进入actor/部署，价值损失不流经深度CNN。训练与导出actor一致性、特权隔离及部分reset测试通过。

辅助目标仍为相机光学系xyz米值及rot6，使用既有xyz MSE与箱体D4对称等价旋转损失，合计乘1.0；不按距离裁剪xyz、不按visibility筛选任何帧。目标的第10维可见性标记保留，只供统计；旧visible_box_pose_loss仅作为历史测试helper保留，当前PPO实际调用all_box_pose_loss。深度、位姿及visibility仍在捕获时成对进入延迟/冻结缓存，避免把旧深度配当前真值。新增box_supervised_fraction（当前1.0）、box_supervised_distance、box_aux_weighted日志，可与box_visible_fraction、box_position和box_rotation比较；全帧且较大系数的长期收敛效果尚需训练观察，本次没有额外限制或掩码改变用户选择。

保留revision21米制深度范围0.1–3m、未命中3m、Gaussian0.02m、stereo0.008–0.03m，headfix阈值fallen_head约0.439m/success_head约0.878m/stand_head约0.932m（直接按精确比例计算）、无early_failure、roll0.5、RSI75/5/20、13段ground_pickup数据与60维AMP、推扰课程/PPO/碰撞资产。足球和wall3/4源码未修改。本次只对明确两项作G1实现，未声称完整复现X2所有训练细节。

checkpoint仍schema2，环境契约升revision22并记录critic维数/末端frame及全帧监督语义。默认严格restore拒绝revision21（旧108维）模型；本次fresh不加载旧权重。旧日志和checkpoint保留。

验证：{count}项CPU通过，包括不可见/7m超量程/相机后方样本梯度、全不可见rollout仍更新pose_head、visibility翻转不改变损失、123维坐标变换/rot6重建、actor隔离、终止前bootstrap及米制延迟配对。20环境采用正式配方更新2轮，保存严格恢复再更新1轮；actor/critic/CNN/pose_head/AMP均更新且数值有限，supervised_fraction全为1。JIT导出重新加载与actor输出一致，ONNX及manifest生成（未独立执行ONNX Runtime）。这些短测模型留在docs下，不作为正式收敛证据。

旧PID{stop['pid']}已停止，最后日志迭代{stop['last_log_iteration']}；最后保存checkpoint为`{stop['last_saved_checkpoint']}`。新PID{s['pid']}，4096环境、seed42、40000轮，fresh，无resume/warm-start。正式检查迭代{s['progress_from']}→{s['progress_to']}，近10轮平均{s['mean_iteration_seconds']:.3f}s，最慢{s['max_iteration_seconds']:.3f}s。model_0核实critic首层512×123、actor首层512×500、辅助系数1.0、全新优化器step20和AMP count61440，源文件/数据hash匹配短测。

正式目录：`{s['run']}`

```bash
tail -f {s['log']}
```

[CPU日志](cpu.log)、[仿真短测](smoke.json)、[正式状态快照](snapshot.json)、[停止记录](stopped_run.json)、[测试回执](receipts.json)。
'''
(DOC/'README.md').write_text(body)
summary=f'2026-10-21：[wall5 critic123与全帧辅助监督revision22]({{link}})：critic新增双掌/双踝/mid360相对骨盆位置15维；辅助系数1.0、所有配对帧，可见性仅诊断。actor仍深度＋本体，保留米制/头高校正/RSI75-5-20。{count}项CPU、20环境更新恢复导出通过。旧PID{stop["pid"]}已停，新PID{s["pid"]}，4096 fresh，检查迭代{s["progress_to"]}，近10轮平均{s["mean_iteration_seconds"]:.3f}s、最慢{s["max_iteration_seconds"]:.3f}s；正式训练进行中，未证明拾箱收敛。'
for file,link in [('projects/README.md','../docs/carrybox/wall5_critic123_aux_20261021/README.md'),('projects/findbox/README.md','../../docs/carrybox/wall5_critic123_aux_20261021/README.md')]:
 p=ROOT/file;old=p.read_text()
 if '[wall5 critic123与全帧辅助监督revision22]' not in old:
  title,rest=old.split('\n',1);p.write_text(title+'\n\n'+summary.format(link=link)+'\n'+rest)
task,_=load_frontmatter(ROOT/f'agent/task/{slug}.md')
changed=set(json.loads((DOC/'before.json').read_text())['source_before'])|{'tests/test_carrybox_critic123_aux.py','projects/README.md','projects/findbox/README.md'}
changed.update(p.relative_to(ROOT).as_posix() for p in DOC.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
changed.add(str((DOC/'artifact_validation.json').relative_to(ROOT)))
changed.update(f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff'))
for kind in ('report','handoff'):
 data=dict(task_id=slug,language='zh-CN',axes=['L'],risk_tier='T2',artifact=kind.upper(),status='DONE',changed_files=sorted(changed),tests=receipts,task_contract_sha256=task_contract_sha256(task))
 if kind=='handoff':data['resume_command']=None
 text=body if kind=='report' else f'''revision22已实现并正式fresh启动，PID{s['pid']}仅为{s['checked_at']}快照。下次操作先核对launch.json、/proc和实时日志。

训练目录：{s['run']}。日志命令：`tail -f {s['log']}`。

critic123=旧108+15个G1末端位置，骨盆link坐标系；actor输入/导出保持深度与本体。全帧辅助coef1.0，不可见/超量程也监督；visibility保留作诊断且配对延迟不变。历史masked helper不再用于当前PPO。新日志box_supervised_fraction必须为1；结合box_aux_weighted和box_position观察后续训练。保留headfix/米制/RSI75-5-20，无early_failure。旧revision21不兼容123维，默认严格load拒绝，正式从头开始。没有改足球或wall3/4。

{count}项CPU、20env更新2＋恢复1轮/导出、4096正式检查{s['progress_to']}轮通过，近10轮平均{s['mean_iteration_seconds']:.3f}s。尚无稳定行走/地面拾箱成功率结论。详见docs/carrybox/wall5_critic123_aux_20261021/README.md及snapshot/receipts；不要把docs短测模型作为正式成果。
'''
 (ROOT/f'agent/{kind}/{slug}.md').write_text('---\n'+'\n'.join(f'{k}: {json.dumps(v,ensure_ascii=False)}' for k,v in data.items())+'\n---\n\n'+text)
print('RECORDS_WRITTEN',s['pid'],s['progress_to'])
