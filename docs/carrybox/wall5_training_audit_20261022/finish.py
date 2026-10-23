from pathlib import Path
import sys, json, hashlib, datetime

R = Path('/home/cao/perceptual_ball')
D = Path(__file__).resolve().parent
slug = 'carrybox-wall5-training-audit-20261022'
sys.path.insert(0, '/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter, task_contract_sha256, validate_paths

s = json.loads((D/'selection.json').read_text())
summary = json.loads((D/'summary.json').read_text())
receipts = json.loads((D/'receipts.json').read_text())['tests']
assert summary['status'] == 'PASS' and all(t['result'] == 'PASS' for t in receipts)
pid = s['launch']['pid']
command = [x.decode() for x in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if x]
assert command == s['launch']['command']
for name, expected in s['launch']['source_sha256'].items():
    assert hashlib.sha256((R/name).read_bytes()).hexdigest() == expected, name
assert hashlib.sha256(Path(s['checkpoint']).read_bytes()).hexdigest() == s['checkpoint_sha256']
(D/'process_status.json').write_text(json.dumps(dict(
    checked_at=datetime.datetime.now().astimezone().isoformat(), pid=pid,
    command=command, source_and_checkpoint_unchanged=True, training_not_restarted=True), indent=2)+'\n')

note = ('revision26只读审查：日志截至401轮，空手近期约6步；model200的39个loco首回合，采样/均值动作约5步，保持reset目标约45步。'
        '确认当前原始力矩平方与PhysHSI除kp后平方同权重，在同批状态相差约1.9万倍；正式空手力矩及动作变化惩罚合计约为walk的1.95倍。'
        'AMP已饱和，但60维FK/坐标对齐，专家重复帧对照不支持将饱和单独归因于历史填充。'
        '14项CPU及64环境只读回放通过；未修改生产或停止/重启PID1796143，未认定单一失稳根因。')
for name, prefix in [('projects/README.md', '../'), ('projects/findbox/README.md', '../../')]:
    p = R/name
    marker = f'{prefix}docs/carrybox/wall5_training_audit_20261022/README.md'
    if marker not in p.read_text():
        head, rest = p.read_text().split('\n', 1)
        p.write_text(head+'\n\n2026-10-22：[wall5训练硬伤与bug审查]('+marker+')：'+note+'\n'+rest)

plan = R/f'agent/plan/{slug}.md'
task_path = R/f'agent/task/{slug}.md'
task, _ = load_frontmatter(task_path)
changed = [str(p.relative_to(R)) for p in D.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
changed += [str(D.relative_to(R)/'artifact_validation.json')]
changed += [f'agent/{kind}/{slug}.md' for kind in ('plan', 'task', 'report', 'handoff')]
changed += ['projects/README.md', 'projects/findbox/README.md']
meta = dict(task_id=slug, language='zh-CN', axes=['L'], risk_tier='T1', status='DONE',
            changed_files=sorted(set(changed)), task_contract_sha256=task_contract_sha256(task),
            tests=receipts, resume_command=None)
body = (note+'\n\n证据及每组分母见 docs/carrybox/wall5_training_audit_20261022/README.md。'
        '测试PASS表示诊断有效，不表示训练收敛。模型在开始时固定200轮、日志最终冻结401轮；没有将两者混为同一时刻。'
        'PPO终止bootstrap、reset前AMP、reward dt、特权隔离等未发现明显错误。辅助全帧系数1.0由用户指定，'
        '本段损失未爆炸，仅保留为远箱风险；未擅自改变。\n')
for kind in ('report', 'handoff'):
    extra = ''
    if kind == 'handoff':
        extra = ('\n本轮为只读审查，没有待恢复执行。下一步若用户要求修复，优先单独校正力矩项语义/尺度，'
                 '再验证空手奖励和稳定性及AMP引导；不要一次替换所有参数，不要仅以重复历史比例屏蔽AMP。'
                 '保持目标仅为被动基线，不能代表稳定控制。正式训练仍在运行，后续先核对实时进程/源码，不凭快照重复启动。\n')
    fields = {**meta, 'artifact': kind.upper()}
    (R/f'agent/{kind}/{slug}.md').write_text('---\n'+'\n'.join(
        k+': '+json.dumps(v, ensure_ascii=False) for k,v in fields.items())+'\n---\n\n'+body+extra)
result = validate_paths(plan, task_path, R/f'agent/report/{slug}.md', R/f'agent/handoff/{slug}.md')
(D/'artifact_validation.json').write_text(json.dumps(result, indent=2)+'\n')
assert result['valid'], result
print('ARTIFACTS_VALID; FORMAL_PROCESS_UNCHANGED', pid)
