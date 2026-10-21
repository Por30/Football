"""Write final project/engineering records after actual formal startup acceptance."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[3]; DOC=Path(__file__).resolve().parent
slug='carrybox-wall5-depth-metres-20261021'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256
s=json.loads((DOC/'snapshot.json').read_text()); smoke=json.loads((DOC/'smoke.json').read_text())
stop=json.loads((DOC/'stopped_run.json').read_text()); receipts=json.loads((DOC/'receipts.json').read_text())['tests']
assert s['status']==smoke['status']=='PASS' and all(t['result']=='PASS' for t in receipts)
body=f'''# wall5 米制深度与噪声修正（revision21）

{s['checked_at']} 状态快照：代码、36项CPU回归、20环境更新/恢复/导出及4096正式启动验收通过。正式训练进行中，尚未评估稳定行走或拾箱成功率。

| 项目 | revision20 | revision21 |
|---|---|---|
| actor深度输入 | 光轴米值除3 | 光轴米值，直接输入 |
| 合法值/未命中 | [0.1/3,1]，未命中1 | [0.1,3]m，未命中3m |
| Gaussian标准差 | 0.06m | 0.02m |
| 立体噪声sigma参数 | 0.024–0.09m | 0.008–0.03m |

噪声数值采用用户最新对照。旧handoff.txt第205/210行显式乘3，当前修改按最新更正仅覆盖wall5；本机没有原始X2环境源码，未声称独立复算X2噪声或全部训练差异。边缘阈值0.15m、边缘/孔洞概率、相机安装/FOV/48×27分辨率/50Hz、4帧历史、延迟/冻结、机身/墙/圆柱遮挡和全部物理设置保持。

米制分支直接读取Warp distance_to_image_plane，NaN/±inf填3并裁剪，再在米制上加噪；缓存和CNN不再除3。可见性同步使用[0.1,3)和nearest Box hit，丢失像素即使保有Box ID也不参与监督。捕获时将深度、光学位姿、visibility整体配对，再延迟/冻结；同一步部分reset不污染幸存环境。

新增env.depth_contract，既有play导出调用自动写入manifest.metadata.depth_contract。导出网络接受与训练相同的米制深度；不再在部署侧除3。契约包括光轴定义、单位/裁剪/未命中、输入形状、历史顺序与噪声。checkpoint升revision21，严格load/default play拒绝旧归一化契约；显式weights-only仍为既有绕过接口，不代表单位兼容。本次没有使用它或恢复旧权重。

用户同时列出critic和辅助监督差异；异步询问范围后，按已告知的建议方案只调整深度及噪声。critic保持108=93本体+3机体线速度+3箱位置+6旋转+3尺寸，独立MLP。handoff的X2 proprio含额外末端位置15维，不能仅为对齐维数补零。当前rot6是相对骨盆旋转的前两列，CPU交叉积重建测试确认与完整相对旋转一致；没有原始X2代码可核验它取哪两列。辅助仍coef0.1、只监督可见且在深度范围内的捕获帧，避免要求深度编码器从看不见的箱子恢复无界真值。它们是保留的G1设计差异，不标为X2完全对齐。

revision20头高校正、无early_failure、独立多原因终止记录、RSI75/5/20、roll0.5、骨盆/近箱阈值、AMP/PPO/数据不变。wall3/4仍是归一化深度及原噪声；football源码未修改。

验证结果：36项CPU通过，覆盖1.5m输入值、非有限/裁剪/miss、两种单位、遮挡/边缘/孔洞、延迟/冻结/同step部分reset、噪声物理标准差、critic旋转和导出隔离。20环境实际Warp无噪声读回逐像素完全相等，范围{smoke['depth_units']['min_m']:.6f}–3m；{smoke['depth_units']['above_one_metre_pixels']}个像素大于1m。实际配方PPO/AMP更新2轮、保存严格恢复后再1轮，参数有限；revision20严格恢复被拒绝；JIT导出并重新加载推理与内存actor一致，ONNX文件及manifest也已生成。ONNX本次仅导出，未独立执行ONNX Runtime。pilot均在docs下，不能作为正式训练/成功率证据。

旧PID{stop['pid']}已停止，最后日志{stop['last_log_iteration']}轮；旧checkpoint `{stop['last_saved_checkpoint']}` 及日志保留，之后未保存的尾部迭代没有恢复。新PID{s['pid']}，4096环境、seed42、40000轮，fresh，无resume/warm-start。已检查到日志迭代{s['progress_to']}，近10轮平均{s['mean_iteration_seconds']:.3f}s，最慢{s['max_iteration_seconds']:.3f}s。首模型确认schema2/revision21、米制/noise/.1辅助系数、108维critic、原头高校正和全新优化器step20/AMP count61440。

正式目录：`{s['run']}`

```bash
tail -f {s['log']}
```

[范围及数值审计](audit.json)、[只读专家核对](expert_brief.json)、[CPU日志](cpu.log)、[真实仿真结果](smoke.json)、[正式启动快照](snapshot.json)、[测试回执](receipts.json)。
'''
(DOC/'README.md').write_text(body)
summary=f'2026-10-21：[wall5米制深度revision21与正式重启]({{link}})：actor直接接收0.1–3m光轴深度，Gaussian0.02m、stereo0.008–0.03m；同步可见性/配对缓存/checkpoint及导出单位，保留critic108与可见监督coef0.1。36项CPU、20环境更新恢复导出通过。旧PID{stop["pid"]}已停，新PID{s["pid"]}，4096 fresh/RSI75-5-20，检查迭代{s["progress_to"]}，近10轮平均{s["mean_iteration_seconds"]:.3f}s、最慢{s["max_iteration_seconds"]:.3f}s。正式训练进行中，未证明拾箱收敛。'
for file,link in [('projects/README.md','../docs/carrybox/wall5_depth_metres_20261021/README.md'),('projects/findbox/README.md','../../docs/carrybox/wall5_depth_metres_20261021/README.md')]:
 p=ROOT/file;old=p.read_text()
 if '[wall5米制深度revision21与正式重启]' not in old:
  title,rest=old.split('\n',1);p.write_text(title+'\n\n'+summary.format(link=link)+'\n'+rest)
task,_=load_frontmatter(ROOT/f'agent/task/{slug}.md')
changed=set(json.loads((DOC/'before.json').read_text())['source_before']) | {'tests/test_carrybox_depth_metres.py','projects/README.md','projects/findbox/README.md'}
changed.update(p.relative_to(ROOT).as_posix() for p in DOC.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
changed.add(str((DOC/'artifact_validation.json').relative_to(ROOT)))
changed.update(f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff'))
for kind in ('report','handoff'):
 data=dict(task_id=slug,language='zh-CN',axes=['P','L'],risk_tier='T2',artifact=kind.upper(),status='DONE',changed_files=sorted(changed),tests=receipts,task_contract_sha256=task_contract_sha256(task))
 if kind=='handoff':data['resume_command']=None
 text=body if kind=='report' else f'''revision21米制深度及噪声修正已完成并通过验证；正式训练仍在运行，PID{s['pid']}仅为{s['checked_at']}快照。下次操作先核对launch.json、/proc及最新日志。\n\n正式run：{s['run']}。日志：`tail -f {s['log']}`。\n\n保留critic108/前两列rot6/visible coef0.1。原用户列出的这两项并未自动全量对齐X2；若用户后续明确要求再单独修改。actor/导出输入必须为米，strict load拒绝旧输入尺度，weights-only不能证明兼容。旧PID已停，历史模型日志保留；不再次执行launch.py。\n\n36项CPU、20环境更新恢复和JIT推理/ONNX导出、4096启动已验收；未评估任务收敛。范围及完整记录见docs/carrybox/wall5_depth_metres_20261021/README.md。'''
 (ROOT/f'agent/{kind}/{slug}.md').write_text('---\n'+''.join(f'{k}: {json.dumps(v,ensure_ascii=False)}\n' for k,v in data.items())+'---\n\n'+text+'\n')
print('Records updated')
