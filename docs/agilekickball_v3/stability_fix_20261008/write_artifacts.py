import json,sys
from pathlib import Path
sys.path.insert(0,'/home/cao/.codex/skills/develop-robotics-engineering/scripts')
from validate_engineering_artifacts import load_frontmatter,task_contract_sha256,validate_paths
root=Path.cwd();out=root/'docs/agilekickball_v3/stability_fix_20261008';slug='agilekickball-v3-stability-fix'
paths={kind:root/'agent'/kind/(slug+'.md') for kind in ('plan','task','report','handoff')}
task,_=load_frontmatter(paths['task'])
start=json.loads((out/'verified_start.json').read_text());metrics=start['metrics']
receipts=json.loads((out/'receipts.json').read_text())['tests'];assert all(x['result']=='PASS' for x in receipts)
scale=json.loads((out/'scale_smoke.json').read_text())
changed=[]
for name in task['allowed_paths']:
 if name=='logs':continue
 path=root/name;before=out/'before'/name
 if path.is_dir() or name.startswith('agent/') or (path.is_file() and (not before.exists() or path.read_bytes()!=before.read_bytes())):changed.append(name)
changed += [str(Path(start['run_dir']).relative_to(root)),str(Path(start['log']).relative_to(root)),str(Path(start['log']).with_suffix('.pid').relative_to(root)),str(Path(scale['run_dir']).relative_to(root))]
common=dict(task_id=task['task_id'],language=task['language'],axes=task['axes'],risk_tier=task['risk_tier'],status='DONE',changed_files=changed,task_contract_sha256=task_contract_sha256(task),tests=receipts)
report=f'''已完成故障诊断、v3 稳定性配置修复、真实恢复验证，并按用户授权重新启动后台正式训练。当前 revision feedback_stable_20261008，PID {start['pid']}，4096 环境、cuda:0、50000 轮、seed 42。启动核验已到日志第 {start['latest_iteration_at_check']} 轮（0 起编号）。DONE 指修复和启动完成，不表示长期训练已经收敛。

失败 run 的 50000 轮恢复数始终为零，最后 1000 轮 episode 58.81 控制步即 1.176 s；实际物理配置与 v2 一致。64 环境各 1500 步、相同 0.4–2 m/s / 1.3–2 m 回放，v2 恢复 855 次，失败 v3 为 0，关闭残差也为 0；采样策略分别 567 与 0。失败主策略本身失稳，不能通过仅关闭残差、降低探索噪声或放宽恢复规则解释/修复。

512 个真实状态中，三个位置 raw logstd 全部处于旧硬截断以下；精度权重约 2981，NLL 对 encoder 梯度范数为同尺度半归一化 MSE 的 1368.6 倍，一步旧 Adam 辅助更新未回退 KL 约 0.0296。它证明硬截断饱和及强梯度共享路径的存在，不是唯一根因的单因素因果证明。旧辅助已接受 199767/200000 个批，不是没有训练。详细审计、配置差异、回放和梯度证据在本次目录。

修复配置：NLL 仅更新预测头、输入特征 detach，主 encoder 仍由 PPO 学习；平滑 logstd [-2,1]；辅助 lr 1e-4、完整动作 KL 上限 .001、残差最大 .1 raw 即 .025 rad。参数进入 typed config 和 schema2 checkpoint。显式从已收敛 v2 迁移主 actor/encoder/critic 与归一化/std/AMP；新头、残差、三个优化器和轮数重新初始化。新课程 E=60000，距离 1.3–2 m、速度 .4–1.1 m/s，扩展未解锁。任务奖励、几何、恢复阈值和课程推进规则不变。

首次真实 smoke 发现 v2 迁移后用从零训练的 PPO 初始 lr .001 会在更新后破坏恢复，因此在允许的 v3 稳定性配置组内将 PPO 初始 lr 降到 1e-5，保留原 adaptive KL 调度、PPO 算法和其余参数。第二次完整启动发现写 initialization.json 前日志目录尚未创建，已显式创建。两次范围内修复后冻结命令全 PASS，失败 receipts/log 单独保存，未放宽恢复断言。

12 项模块测试、159 项任务/legacy 回归通过，覆盖初始化动作/critic 逐元素一致、AMP 迁移、独立辅助梯度、完整参数/Adam 回退、平滑有界方差、非零残差 TorchScript/ONNX、schema/恢复兼容。16 环境各 1000 步真实恢复：迁移后 98 次，更新和续训后 92 次，无倒地终止。4096 环境正式 PPO 参数 100 轮短训通过，末轮 episode 约 30.16 s；辅助主encoder更新数0，预测头每轮4批，全部有限。100 轮后同条件 64 环境回放恢复 900 次、走出边界终止12次、无倒地；它继承 v2 权重，不能当作新增反馈机制优于 v2 的证据。

正式进程核验：独立 session/PID、实际 CLI 与 saved agent.yaml、首个有限 checkpoint、schema2、warm-start 来源与 SHA256、辅助 optimizer 均正常。第 {start['latest_iteration_at_check']} 轮日志 episode 均值 {metrics['Train/mean_episode_length']*.02:.2f} s，恢复发球累计指标 {metrics['AgileKickball/recovered_serves']:.2f}（rollout 平均值，不是单次窗口的整数计数）；预测头接受 {metrics['Loss/aux/predictor_updates']:.0f}/4 批，NLL encoder 更新0，完整辅助阶段 KL {metrics['Loss/aux/stage_monitor_kl']:.8g}。没有 NaN/OOM/Traceback。

日志：{start['log']}\n模型目录：{start['run_dir']}\n启动命令：bash scripts/rsl_rl/train_agilekickball_v3.sh。当前已运行，勿重复启动。

限制：新训练是 v2 权重初始化而非 scratch；后续论文须显式计算预训练预算、固定评测分布并做多种子/消融。平滑方差未校准、短测不是长期收敛证明。旧模型、日志、反馈/Outcome 归档任务保留；v2 和共享物理/PPO源码哈希与此前快照一致。51 个训练源文件及 SHA256 已归档。
'''
handoff=f'''当前目标已完成：诊断、修复、验证并后台启动新 v3。PID {start['pid']}，revision feedback_stable_20261008，当前已核验第 {start['latest_iteration_at_check']} 轮。launch.json 记录 start_ticks 和独立 session；后续先核对进程身份，禁止重复启动/覆盖旧run。DONE 不意味着50000轮训练已完成。

新入口 scripts/rsl_rl/train_agilekickball_v3.sh 默认 --warm_start_v2 源 v2 model_49999.pt，独立新 run；--resume 时脚本不传 warm-start，两者互斥。runner.warm_start_from_v2 先验证版本/形状/finite/AMP及残差零输出，再加载主网络权重，优化器/课程/轮数不迁移。initialization.json 和checkpoint记录 source SHA256。

关键配置：PPO 初始 lr1e-5（adaptive调度），NLL lr1e-4，KL .001，update_encoder=false，smooth logstd[-2,1]，残差上限 .1 raw。ball_distribution 的 detach_features 只用于辅助，PPO仍可更新原encoder。Loss/aux/encoder_updates 应为0，aux/predictor_updates才是新辅助接受数。禁止重新启用旧head-only fallback；拒绝trial后恢复全部本次辅助参数及深拷贝Adam。

旧失败版本可通过 Template-Perceptual-Ball-AgileKickball-v3-StateFeedback-20261006 回放，默认策略/算法保留schema1；旧Outcome任务也保留。新任务课程revision与schema2会拒绝普通resume旧模型，不能把warm-start冒充断点续训。新课程起点由startup参数initial_exposure_steps=60000定义，物理阈值与v2相同。

冻结三命令最终PASS，失败历史保留；100轮4096短训及同条件修复后回放已通过。源文件在 docs/agilekickball_v3/stability_fix_20261008/source_snapshot/。完整证据包括 comparison/config_differences/replay/probe/diagnosis/smoke/scale_smoke/replay_repaired/verified_start JSON。修复后同条件恢复900次与继承v2有关，不足以声称方法提升。

状态命令：tail -n 120 {start['log']}\n进程命令：ps -p {start['pid']} -o pid,sid,etime,args\n模型目录：{start['run_dir']}\n关注early episode长度、累计恢复、每6000控制步的课程窗口、预测头更新、NLL主encoder更新是否为0、动作修正幅度、KL及finite。暂未验证长期收敛；保持旧v2基线和所有旧日志。无需恢复本轮工作或再次启动训练。
'''
for kind,body in [('report',report),('handoff',handoff)]:
 front={**common,'artifact':kind.upper()}
 if kind=='handoff':front['resume_command']=None
 paths[kind].write_text('---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in front.items())+'\n---\n\n'+body)
result=validate_paths(*[paths[k] for k in ('plan','task','report','handoff')])
(out/'artifacts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
assert result['valid'],result
print(json.dumps(result,ensure_ascii=False))
