"""Write the launch report from successful, recorded runtime evidence."""
from pathlib import Path
import json
import sys

DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
SLUG = 'carrybox-wall5-roll05-start-20261019'
s = json.loads((DOC / 'snapshot.json').read_text())
r = json.loads((DOC / 'launch.json').read_text())
receipts = json.loads((DOC / 'receipts.json').read_text())['tests']
assert s['status'] == 'PASS' and all(t['result'] == 'PASS' for t in receipts)
summary = (f"wall5已按用户新指令从零正式启动，PID{s['pid']}，4096环境、seed42、40000轮，"
           f"无resume/warm-start。检查时间{s['checked_at']}，迭代{s['progress_from']}→{s['progress_to']}；"
           f"最近10轮平均{s['mean_iteration_seconds']:.3f}秒、最慢{s['max_iteration_seconds']:.3f}秒。"
           "首checkpoint确认revision15＋roll0.5、RSI80/0/20、13段60维AMP、独立108维critic；"
           "actor仍深度＋本体，增量push与1.0/multiply摩擦已生效。优化器及AMP统计是全新初始化，参数有限。"
           "生产代码未修改，先前未通过的loco控制候选未启用。训练进行中，尚未证明站走或拾箱收敛。")
metrics = '\n'.join(f'- `{k}`：{v:.4f}' for k, v in s['latest_logged_metrics'].items())
body = f"""# wall5 roll0.5正式从零训练

{summary}

用户在此前修复候选撤回、随后将roll改为0.5rad之后明确要求重新启动。此次执行现有配置；没有重新试参、复用失败候选或把旧静止验收改为通过。

Run：`{s['run']}`。

查看终端日志：

```bash
tail -f '{s['log']}'
```

本次实际启动命令（正在运行，不应重复执行）：

```bash
cd /home/cao/perceptual_ball
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${{PYTHONPATH:-}}"
export OMNI_KIT_ACCEPT_EULA=YES
{' '.join(r['command'])}
```

启动期指标（分技能mean_steps是累计统计，不能当作近期独立成功率）：

{metrics}

完整启动验收见[snapshot.json](snapshot.json)和[真实回执](receipts.json)；PID、命令、AMP manifest hash、8个相关源码hash见[launch.json](launch.json)，对应源码保存在`source_snapshot/`。首model_0的PPO/AMP优化器step均20，Normalizer count61440，确认fresh；没有从docs验证模型加载权重。最近10轮均在6秒内。

roll0.5的14项CPU检查沿用[前一变更验收](../wall5_roll05_20261019/README.md)，推扰/摩擦的仿真与更新恢复沿用[revision15检查](../wall5_push_20261019/README.md)。此次冻结命令`bash docs/carrybox/wall5_roll05_start_20261019/verify.sh`仅只读验证新正式进程。启动成功不代表此前快速倾倒已修复，后续应持续看loco/hold各自长度、朝箱移动和地面拾取成功，不能只看总回合长度。

时间/PID/迭代是上述时刻快照，后续操作前重新核对实际状态；本任务没有停止其他进程。
"""
(DOC / 'README.md').write_text(body)
entry = ('2026-10-19：[{title}]({link})：4096环境fresh、roll0.5，PID{pid}，'
         '检查迭代{iteration}，最近10轮平均{mean:.3f}秒/最慢{maximum:.3f}秒；'
         '首checkpoint确认revision15、非对称AC、RSI80/0/20及13段60维AMP。'
         '用户明确重启，原控制候选保持撤回；训练进行中，未证明收敛。\n\n')
for name, prefix in [('projects/README.md', '../'), ('projects/findbox/README.md', '../../')]:
    path = ROOT / name
    text = path.read_text()
    line = entry.format(title='wall5 roll0.5正式重启', link=prefix+'docs/carrybox/wall5_roll05_start_20261019/README.md',
        pid=s['pid'], iteration=s['progress_to'], mean=s['mean_iteration_seconds'], maximum=s['max_iteration_seconds'])
    assert 'wall5_roll05_start_20261019/README.md' not in text
    title, rest = text.split('\n\n', 1)
    path.write_text(title + '\n\n' + line + rest)
sys.path.insert(0, '/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter, task_contract_sha256
task, _ = load_frontmatter(ROOT / f'agent/task/{SLUG}.md')
metadata = dict(task_id=SLUG, language='zh-CN', axes=['A'], risk_tier='T1', status='DONE',
    changed_files=task['allowed_paths'], task_contract_sha256=task_contract_sha256(task), tests=receipts, resume_command=None)
for kind in ('report', 'handoff'):
    data = dict(metadata, artifact=kind.upper())
    text = '---\n' + '\n'.join(k+': '+json.dumps(v, ensure_ascii=False) for k, v in data.items()) + '\n---\n\n'
    text += summary + '\n\n' + f"Run：{s['run']}。日志：{s['log']}。\n\n"
    text += '本任务完成的是用户明确要求的正式启动及运行核验，不是修复控制问题或完成40000轮训练。进程留在后台，后续先核对launch.json及真实PID命令；不得重复启动或用文档快照推断实时状态。详细证据、分技能初期指标和复现命令见docs/carrybox/wall5_roll05_start_20261019/README.md。\n'
    (ROOT / f'agent/{kind}/{SLUG}.md').write_text(text)
print(summary)
