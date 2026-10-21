"""Publish the verified fresh-run status; never start or stop a process."""
from pathlib import Path
import json
import sys

DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
sys.path.insert(0, '/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter, task_contract_sha256

snapshot = json.loads((DOC / 'snapshot.json').read_text())
receipts = json.loads((DOC / 'receipts.json').read_text())['tests']
launch = json.loads((DOC / 'launch.json').read_text())
stopped = json.loads((DOC / 'stopped_run.json').read_text())
assert snapshot['status'] == 'PASS' and all(t['result'] == 'PASS' for t in receipts)
assert stopped['status'] == 'exited' and snapshot['initialization'] == 'fresh'
summary = (
    f"旧revision17 PID{stopped['pid']}已退出，历史日志和model_14800.pt保留。"
    f"新版revision18三维距离训练已从零启动，4096环境、seed42、40000轮，"
    f"PID{snapshot['pid']}；检查至{snapshot['progress_to']}轮，最近10轮平均"
    f"{snapshot['mean_iteration_seconds']:.3f}秒、最慢{snapshot['max_iteration_seconds']:.3f}秒。"
    "首模型确认XYZ距离0.7m、schema2/revision18、非对称AC及13段60维AMP，"
    "优化器/Normalizer为全新初始化。正式训练进行中，尚未证明抱箱成功。"
)
body = f"""# wall5 revision18 从零正式重启

{summary}

时间：{snapshot['checked_at']}，Asia/Tokyo。用户明确要求停止当前训练并从头开始。
SIGTERM后旧进程尚未退出，核对PID完整命令和进程起始时间后发送SIGINT；
确认进程消失、显存释放后才启动新训练。旧模型和日志未删除。
[停止记录](stopped_run.json)、[启动记录](launch.json)、[正式运行验收](snapshot.json)。

新训练采用上一任务已验证的revision18：骨盆连杆原点到箱心XYZ距离，
0.7m奖励门控；水平行走方向、AMP水平封顶、RSI固定80/0/20、
roll0.5、13段ground_pickup数据、actor深度＋本体、独立108维特权critic保持。
本次不改生产源码或超参。启动前比对revision18源码hash、已有43项CPU和4环境
PPO/AMP测试记录，并核验13个数据文件hash；启动时无其他train/play进程，
可用显存{launch['free_mib_before']}MiB。

命令没有resume、warm_start或checkpoint参数；保存配置resume=false。
首个model_0.pt中策略和AMP优化器均为20个更新步，AMP Normalizer count=61440，
匹配全新训练的首轮更新；参数和优化器有限值检查通过。
源代码快照见source_snapshot/，hash见launch.json。

正式run：

```text
{snapshot['run']}
```

首个模型：

```text
{snapshot['checkpoint']}
```

查看实时日志：

```bash
tail -n 100 -f "{snapshot['log']}"
```

查看进程：

```bash
ps -p {snapshot['pid']} -o pid,etime,args
```

验收命令（只读核验现有训练，不会重新启动）：

```bash
bash docs/carrybox/wall5_v18_fresh_20261020/verify.sh
```

启动脚本有launch.json防重复保护，不应再次执行。下一次操作前重新核对实际PID、
命令和日志；此处迭代数是时间快照。启动核验不代表收敛或地面拾箱成功。
"""
(DOC / 'README.md').write_text(body)
for relative, prefix in [('projects/findbox/README.md', '../../'), ('projects/README.md', '../')]:
    path = ROOT / relative
    title, rest = path.read_text().split('\n', 1)
    link = prefix + str(DOC.relative_to(ROOT)) + '/README.md'
    entry = f'\n2026-10-20：[wall5 revision18三维距离从零正式重启]({link})：{summary}\n'
    assert link not in rest, 'Already published; do not duplicate status'
    path.write_text(title + '\n' + entry + rest)

slug = 'carrybox-wall5-v18-fresh-20261020'
task, _ = load_frontmatter(ROOT / f'agent/task/{slug}.md')
changed = [f'agent/{kind}/{slug}.md' for kind in ('plan', 'task', 'report', 'handoff')]
changed += ['projects/README.md', 'projects/findbox/README.md']
changed += [str(p.relative_to(ROOT)) for p in DOC.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
changed += [str(Path(snapshot['log']).relative_to(ROOT)),
            str(Path(snapshot['checkpoint']).relative_to(ROOT)),
            str((Path(snapshot['run']) / 'params/env.yaml').relative_to(ROOT)),
            str((Path(snapshot['run']) / 'params/agent.yaml').relative_to(ROOT))]
common = dict(task_id=slug, language='zh-CN', axes=['L'], risk_tier='T2', status='DONE',
              changed_files=sorted(set(changed)), task_contract_sha256=task_contract_sha256(task),
              tests=receipts, resume_command=None)
for kind, content in (
    ('report', summary + '\n\n验收证据和日志命令见docs/carrybox/wall5_v18_fresh_20261020/README.md；'
     '正式训练持续运行，本任务完成停止旧run、从零启动新run和启动核验，没有完成40000轮或评估成功率。'),
    ('handoff', summary + '\n\n新日志：' + snapshot['log'] + '\n\n新run：' + snapshot['run'] +
     '\n\n不要重复执行launch.sh；下一次任务先核对launch.json的真实PID和完整命令。'
     '新run没有加载任何旧checkpoint。生产源码沿用上一任务revision18并已有快照，'
     '既有暂存修改和历史工件保留。长期稳定性和拾箱能力需要后续独立回放，不能用启动PASS代替。')
):
    data = dict(common, artifact=kind.upper())
    (ROOT / f'agent/{kind}/{slug}.md').write_text(
        '---\n' + '\n'.join(f'{k}: {json.dumps(v, ensure_ascii=False)}' for k, v in data.items())
        + '\n---\n\n' + content + '\n')
print(summary)
