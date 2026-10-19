from pathlib import Path
import json,sys
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2];slug='carrybox-wall5-asymmetric-20261019'
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
tests=[json.loads((DOC/f'receipts_{name}.json').read_text())['tests'][0] for name in ('cpu','smoke','launch')]
assert all(t['result']=='PASS' for t in tests)
(DOC/'receipts.json').write_text(json.dumps({'schema_version':'robotics-engineering-test-receipts.v1','tests':tests},indent=2)+'\n')
s=json.loads((DOC/'snapshot.json').read_text());old=json.loads((DOC/'stopped_run.json').read_text())
body=f'''# Wall5非对称Actor–Critic与正式重启（2026-10-19）

用户明确要求仅critic使用特权信息。wall5已升级revision14，actor及部署接口保持深度与本体；critic独立MLP，无深度输入，也不向深度CNN反传value loss。

| 分支 | 实际输入 | 网络 |
|---|---|---|
| Actor | 4帧本体93×4=372；4帧27×48深度 | 原CNN输出128，与本体拼成500；MLP512/256/256→29动作 |
| Critic | 当前本体93＋机体线速度3＋箱子相对位置3＋相对旋转6＋完整尺寸3=108 | 独立MLP108→512→256→256→1 |
| 辅助位姿头 | actor深度latent128 | 原9维位姿预测，保留可见性配对mask及coef0.1 |

本体93为角速度3（×0.25）、投影重力3、关节位置偏差29、关节速度偏差29（×0.05）、上一动作29。critic用当前帧；actor保持4帧历史，不含线速度。critic新增速度为pelvis link原点的机体系速度m/s；箱子位置为同坐标系米制相对位置，旋转为pelvis逆姿态乘箱子姿态的旋转矩阵前两列，尺寸为箱子局部完整边长（当前0.30×0.30×0.25m）。critic真值不施加相机遮挡、延迟或AMP的0.7m截断；这些真值不会进入actor、pose head输入或部署导出。

只修改三个wall5生产文件。新增critic_state观测、独立critic类、PPO快路和reset前critic快照；timeout bootstrap取本回合终止状态，避免使用重置后的箱子/机器人状态。新模型环境契约为schema2/revision14，旧revision13完整resume及完整权重warm-start因critic形状/契约变化不兼容；本次按用户要求fresh。

AMP仍为ground_pickup的13段、60维×10窗口、running normalization；AMP采样40/40/20，RSI80/0/20，奖励/PPO超参/深度/全身碰撞均保持。wall3/wall4、CarryBox-v0和football生产接口未改。

验证：31项CPU通过（含6项非对称专用检查）；4环境真实PPO/AMP完整配方2＋恢复1轮通过，含强制timeout、部分reset、终止快照、有限更新、严格恢复、TorchScript/ONNX导出与wall4配置隔离。正式4096检查于{s['checked_at']}通过：迭代{s['progress_from']}→{s['progress_to']}，最近10轮平均{s['mean_iteration_seconds']:.3f}秒，最慢{s['max_iteration_seconds']:.3f}秒。

旧PID{old['pid']}已停止，旧模型保留至`{old['last_checkpoint']}`。新PID{s['pid']}，4096环境、seed42、40000轮、从零初始化；首model_0中PPO/AMP优化器均step20，AMP Normalizer count{s['initial_amp_normalizer_count']}，确认没有继承旧训练状态。训练已启动，尚无收敛结论。

新run：`{s['run']}`

```bash
tail -f '{s['log']}'
```

启动过程中旧进程退出后的GPU显存释放有短暂延迟，复查空闲后才启动。首个新进程因未加载Isaac Sim环境在导入阶段退出、没有训练迭代；补齐显式setup_conda_env.sh及导入预检后启动当前run。失败回执、日志和诊断均保留，没有盲目循环重启。CPU首次检查仅测试脚本误用元数据键num_clips，修正为实际clip_count后通过，原失败记录保留。

证据：production_changes.json记录三个生产文件hash；expert_review.md为独立只读审查；receipts.json为三条冻结命令最终回执，smoke.json为真实仿真，snapshot.json为正式运行快照，launch.json/stopped_run.json记录进程身份。验证模型仅在本docs目录，正式run没有加载它。
'''
(DOC/'README.md').write_text(body)
short=f"{s['checked_at'][:16].replace('T',' ')} JST：[wall5非对称AC与4096从零重启]({{link}})：revision14仅critic使用108维本体/线速度/箱位姿尺寸真值，独立MLP；actor仍372维本体＋4帧深度。31项CPU、4环境2＋1轮更新恢复导出及正式启动核验通过；旧PID{old['pid']}已停止，新PID{s['pid']}，检查至{s['progress_to']}轮，最近10轮平均{s['mean_iteration_seconds']:.3f}秒/最慢{s['max_iteration_seconds']:.3f}秒。AMP13段/RSI80-0-20保持，训练进行中，未证明收敛。"
for name,link in [('projects/README.md','../docs/carrybox/wall5_asymmetric_20261019/README.md'),('projects/findbox/README.md','../../docs/carrybox/wall5_asymmetric_20261019/README.md')]:
    p=ROOT/name;text=p.read_text();head,rest=text.split('\n',1)
    if link not in rest:rest='\n'+short.format(link=link)+'\n'+rest
    if name=='projects/findbox/README.md':
        old_current='当前wall5代码为revision13，用户已于2026-10-18启动4096环境fresh正式训练。12:33 JST PID3804340连续推进到第10轮，model_0确认RSI80/0/20、60维AMP/Normalizer及新版PPO已生效；第1–10轮平均7.001秒，超过6秒目标，尚未证明收敛。本次只读核验，没有修改或重启训练。历史短测模型仍仅作工程验证。'
        rest=rest.replace(old_current,f"当前wall5为revision14非对称AC，{s['checked_at']}核验正式PID{s['pid']}至{s['progress_to']}轮；4096环境fresh，最近10轮平均{s['mean_iteration_seconds']:.3f}秒。critic独立108维特权MLP；actor仍深度＋本体，AMP13段/RSI80/0/20。旧PID3812053已停止，所有旧模型保留；历史短测模型仅作工程验证。")
        rest=rest.replace('actor/critic只读取深度与本体观测。箱子真值用于监督、奖励及成功判定；wall5 revision12按用户要求也将有界箱相对位置加入训练专用60维AMP，基线/wall3/4仍用原本体AMP。上述信息都不进入actor/critic。持箱参考动作只提供动作先验，不增加搬运目标点或放下阶段。','CarryBox-v0及wall3/4的actor/critic只读取深度与本体。wall5 revision14按用户明确要求采用非对称AC：actor仍只读深度与本体，critic为当前本体＋机体线速度＋箱子相对位姿/尺寸真值的108维独立MLP，特权信息不进入actor或部署导出。wall5另保留训练专用60维任务AMP及可见性配对辅助监督，基线/wall3/4仍用原AMP。持箱参考不增加搬运目标点或放下阶段。')
    else:
        lines=rest.splitlines()
        for i,line in enumerate(lines):
            if line.startswith('| CB-003 |'):lines[i]=f"| CB-003 | 搬箱子 | 正式训练 | wall5 revision14运行中 | [非对称AC，4096 fresh](../docs/carrybox/wall5_asymmetric_20261019/README.md)；{s['checked_at'][:16]}核验PID{s['pid']}至{s['progress_to']}轮，平均{s['mean_iteration_seconds']:.3f}秒/轮；未证明收敛 |"
        rest='\n'.join(lines)+'\n'
    p.write_text(head+'\n'+rest)
task,_=load_frontmatter(ROOT/f'agent/task/{slug}.md')
changed=list(json.loads((DOC/'production_changes.json').read_text()))+['AGENTS.md','projects/README.md','projects/findbox/README.md','tests/test_carrybox_asymmetric.py']
changed += [f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')]
changed += [str(p.relative_to(ROOT)) for p in DOC.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
changed += [str((DOC/'artifact_validation.json').relative_to(ROOT)),str(Path(s['log']).relative_to(ROOT)),str(Path(old['log']).relative_to(ROOT))]
changed += [str(p.relative_to(ROOT)) for p in Path(s['run']).rglob('*') if p.is_file()]
failed=json.loads((DOC/'launch_failed_import.json').read_text());changed.append(str(Path(failed['log']).relative_to(ROOT)))
common={k:task[k] for k in ('task_id','language','axes','risk_tier')}
common.update(status='DONE',changed_files=sorted(set(changed)),task_contract_sha256=task_contract_sha256(task),tests=tests)
for kind in ('report','handoff'):
    meta=dict(common,artifact=kind.upper())
    if kind=='handoff':meta['resume_command']=None
    content=body if kind=='report' else f"wall5 revision14非对称AC已实现并通过CPU/实际仿真/正式启动三项验收。actor不变，critic108维独立MLP及pre-reset快照。旧PID3812053停止；新PID{s['pid']}，4096 fresh，run={s['run']}，log={s['log']}。核验{s['checked_at']}至{s['progress_to']}轮，平均{s['mean_iteration_seconds']:.3f}秒。所有工程修改仅三个wall5文件；AMP/RSI/奖励/相机与其他任务保持。AGENTS与项目入口已更新特权critic例外。当前任务无待办；训练进行中，未评估收敛。后续操作先复核实时进程，不直接重跑launch.sh。详见docs/carrybox/wall5_asymmetric_20261019/README.md。"
    (ROOT/f'agent/{kind}/{slug}.md').write_text('---\n'+''.join(f'{k}: {json.dumps(v,ensure_ascii=False)}\n' for k,v in meta.items())+'---\n\n'+content+'\n')
result=validate_paths(*(ROOT/f'agent/{k}/{slug}.md' for k in ('plan','task','report','handoff')))
(DOC/'artifact_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');assert result['valid'],result
print(json.dumps(dict(validation=result,pid=s['pid'],iteration=s['progress_to'],mean_seconds=s['mean_iteration_seconds'],max_seconds=s['max_iteration_seconds'],log=s['log']),ensure_ascii=False))
