"""Package executed evidence after formal startup acceptance; no simulator work."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
DOC = Path(__file__).resolve().parent
sys.path.insert(0, '/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter, task_contract_sha256

task_path = ROOT/'agent/task/carrybox-wall5-semantic-20261020.md'
task, _ = load_frontmatter(task_path)
receipts = json.loads((DOC/'receipts.json').read_text())['tests']
assert all(t['result'] == 'PASS' for t in receipts)
s = json.loads((DOC/'snapshot.json').read_text())
assert s['status'] == 'PASS' and s['revision'] == 19
plan_path = ROOT/'agent/plan/carrybox-wall5-semantic-20261020.md'
plan, plan_body = load_frontmatter(plan_path)
plan['status'] = 'DONE'
plan_path.write_text('---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False)
    for k,v in plan.items())+'\n---\n'+plan_body+
    '\n\n实现、短测和用户授权的正式启动验收完成；40000轮训练仍在后台进行。具体数值与时间快照见同任务Report/Handoff。\n')
summary = (
    f"G1参考几何标定后，3D接近阈值0.7→0.783688m，保持X2参考水平范围约0.441m；"
    f"高度阈值/指数尺度同步适配，standup/search改pelvis参考，移除独立稳定奖励及walk乘法。"
    f"roll0.5、RSI80/20、非对称AC/深度/AMP/PPO保持。48项CPU及4环境2＋1轮更新恢复通过。"
    f"旧PID553495已退出，4096 fresh新PID{s['pid']}，检查至{s['progress_to']}轮，"
    f"最近10轮平均{s['mean_iteration_seconds']:.3f}s、最慢{s['max_iteration_seconds']:.3f}s。"
    f"首模型确认schema2/revision19及全新优化器/Normalizer。正式训练进行中，尚未评估收敛或地面拾箱成功。"
)
for path, prefix in ((ROOT/'projects/README.md', '../'), (ROOT/'projects/findbox/README.md', '../../')):
    content = path.read_text()
    line = f"2026-10-20：[wall5 revision19 G1奖励语义适配与从零重启]({prefix}docs/carrybox/wall5_semantic_20261020/README.md)：{summary}\n\n"
    title, rest = content.split('\n', 1)
    assert 'wall5 revision19 G1奖励语义适配与从零重启' not in rest, 'Already packaged'
    path.write_text(title+'\n\n'+line+rest.lstrip('\n'))

with (DOC/'README.md').open('a') as f:
    f.write(f"""
## 正式训练状态（{s['checked_at']} 快照）

{summary}

当前run：`{s['run']}`。启动时间/精确命令见launch.json；源码快照和hash已存档。运行预算40000轮，seed42，无resume/warm-start。首模型`model_0.pt`的PPO/AMP optimizer step均为20，AMP Normalizer count61440，13段数据manifest一致。旧run模型与日志均保留。两次工具修复分别是显存释放等待和只读验收导入，最终三条冻结测试全部通过。

```bash
tail -f "{s['log']}"
```

新训练的启动和持续迭代已经验收；长期存活、接近箱子、地面拾取成功率尚未独立评估。几何标定只适用于当前G1资产和箱体，后续更换构型/尺寸应重新核定。
""")

source_files = [
    'source/perceptual_ball/perceptual_ball/carrybox_reward_geometry.py',
    'source/perceptual_ball/perceptual_ball/carrybox_walled.py',
    'source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py',
    'source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py',
    'source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py',
    'source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py',
    'tests/test_carrybox_reward_geometry.py', 'tests/test_carrybox_reset_bug.py',
    'projects/README.md', 'projects/findbox/README.md',
]
files = source_files + [str(p.relative_to(ROOT)) for p in DOC.rglob('*')
                        if p.is_file() and '__pycache__' not in p.parts]
files += [f'agent/{kind}/carrybox-wall5-semantic-20261020.md' for kind in ('plan','task','report','handoff')]
files += [str(Path(s[key]).relative_to(ROOT)) for key in ('checkpoint','log')]
files += [str((Path(s['run'])/'params'/name).relative_to(ROOT)) for name in ('env.yaml','agent.yaml')]
meta = {key: task[key] for key in ('task_id','language','axes','risk_tier')}
meta.update(status='DONE', changed_files=sorted(set(files)), task_contract_sha256=task_contract_sha256(task),
            tests=receipts, resume_command=None)
for kind in ('report','handoff'):
    front = dict(meta, artifact=kind.upper())
    body = summary + (
        '\n\n本次完成实现、短测及正式启动，未完成40000轮训练。CPU与仿真检查不提供收敛保证；'
        '删除稳定奖励后应跟踪loco/hold分组完成长度、loco成功率、carryup/standup贡献和倾倒率。'
        'AMP/actor/critic接口、数据、动作正则和推扰课程均不变；wall3/4保留默认行为。\n\n'
        f'查看日志：`tail -f "{s["log"]}"`。当前训练已在后台运行，不要再次启动同一任务。'
        '后续状态必须只读核验真实进程，不能把此快照当作实时状态。完整参数和证据见'
        'docs/carrybox/wall5_semantic_20261020/README.md。显存门禁及验收导入两次失败回执保留，'
        '最终回执为三项PASS；没有放宽资源门槛或测试断言。旧rev18严格恢复已拒绝，'
        '历史模型保留在原run。新增profile/数据几何变动应重新标定并更新契约。\n'
    )
    (ROOT/f'agent/{kind}/carrybox-wall5-semantic-20261020.md').write_text(
        '---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in front.items())+'\n---\n\n'+body)
print(summary)
