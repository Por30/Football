from pathlib import Path
import hashlib
import importlib.util
import json
import sys

root = Path('/home/cao/perceptual_ball')
out = root / 'docs/agilekickball_v4/return_to_sender_20261012'
spec = importlib.util.spec_from_file_location('contracts', '/home/cao/.codex/skills/develop-robotics-engineering/scripts/validate_engineering_artifacts.py')
contract = importlib.util.module_from_spec(spec); spec.loader.exec_module(contract)
task_path = root / 'agent/task/agilekickball-v4-return.md'
task, _ = contract.load_frontmatter(task_path)
receipts = json.loads((out / 'receipts.json').read_text())['tests']
assert all(row['result'] == 'PASS' for row in receipts)
verified = json.loads((out / 'verified_start.json').read_text())
assert verified['pid_alive'] and verified['last_iteration'] >= 10 and verified['finite_checkpoint']
changed = [p for p in task['allowed_paths'] if p.endswith(('.py', '.sh'))]
changed += [p for p in task['allowed_paths'] if p.startswith('agent/')]
changed += ['docs/agilekickball_v4/README.md', 'docs/agilekickball_v4/return_to_sender_20261012',
            'logs/rsl_rl/agilekickball_v4', 'logs/rsl_rl/agilekickball_v4_smoke']
base = {key: task[key] for key in ('task_id', 'language', 'axes', 'risk_tier')}
base.update(status='DONE', changed_files=changed, task_contract_sha256=contract.task_contract_sha256(task), tests=receipts)
def write(path, data, body):
    path.write_text('---\n' + '\n'.join(k + ': ' + json.dumps(v, ensure_ascii=False) for k, v in data.items()) + '\n---\n\n' + body + '\n')
body = f'''v4 `return_to_sender_20261012` 已建立，原 v2/v3 配置文件 hash 保持一致。每轮发球点定义反向目标门，半宽 0.6→0.2 m；有效脚击球代理、单向线段插值穿越、球高/速度阈值防错误计分。奖励替换径向返回为源点质量，加入单次目标命中；保留 v3 网络、观察、空间边界、恢复条件及训练稳定设置。独立目标指标和完成轮次分母避免用 kick proxy 冒充回传成功。

完整加载最新 v3 model_49999.pt（含预测头/反馈/归一化/AMP），优化器、计数、速度及方向课程新建。167 项状态/旧 v3 回归与 12 项反馈测试通过；真实 CPU 仿真 3 个 PPO 更新、精确初始化、恢复/回放/课程冻结通过；4096 环境 100 轮正式入口短训通过。首轮 smoke 因测试复用 inference normalizer 缓存失败；仅将 play 验证改为新建 runner，第二次冻结检查全部通过，首轮失败回执保留。正式启动第一次在模拟器开始运行前发生原生 malloc 堆错误，未进入任务更新；无 OOM 或残留训练进程证据，日志保留在 formal_start_attempt1.log。资源检查后保持全部任务参数不变做一次重启；原生错误根因尚未确定，不能宣称已根治。

正式训练 PID {verified['pid']}，run `{verified['run']}`，核验已到 iteration {verified['last_iteration']}，checkpoint 有限，记录新版本和 v3 初始化来源。目标 50000 次迭代、4096 环境、seed42。启动/测试/source snapshot 证据均在 docs/agilekickball_v4/return_to_sender_20261012；运行日志 `{verified['log']}`。

已完成的是任务实现和训练启动，正式训练仍在后台运行。短测不证明已收敛或学会精确回传。0.2 m 是最终目标门半宽，不是已经达到的实际误差；接触采用脚邻近速度变化代理。原路返回落实为回到发球点附近，不是逐点反演轨迹。'''
write(root / 'agent/report/agilekickball-v4-return.md', dict(base, artifact='REPORT'), body)
write(root / 'agent/handoff/agilekickball-v4-return.md', dict(base, artifact='HANDOFF', resume_command=None), body + f'''\n\n下一步只读监控 `tail -n 120 {verified['log']}`。不要重复启动。完成后用固定球速、固定 ±0.2m 门、完成轮次分母做回传评估；当前指标为训练分布，需区分课程半宽和固定门命中。若进程意外终止，只可使用同 v4 checkpoint 执行 `bash scripts/rsl_rl/train_agilekickball_v4.sh --resume --checkpoint <v4模型绝对路径>`；脚本自动去掉 warm-start。''')
result = contract.validate_paths(root / 'agent/plan/agilekickball-v4-return.md', task_path,
    root / 'agent/report/agilekickball-v4-return.md', root / 'agent/handoff/agilekickball-v4-return.md')
(out / 'artifacts.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
assert result['valid'], result
