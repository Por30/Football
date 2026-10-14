---
task_id: "AGILE-V3-STABILITY-FIX-20261008"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/state_feedback.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/export.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "tests/test_state_feedback.py", "tests/test_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "scripts/rsl_rl/train_agilekickball_v3.sh", "docs/agilekickball_v3/README.md", "README.md", "scripts/rsl_rl/train.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_feedback_legacy_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3_feedback_legacy.py", "docs/agilekickball_v3/stability_fix_20261008", "agent/plan/agilekickball-v3-stability-fix.md", "agent/task/agilekickball-v3-stability-fix.md", "agent/report/agilekickball-v3-stability-fix.md", "agent/handoff/agilekickball-v3-stability-fix.md", "logs/rsl_rl/agilekickball_v3/2026-10-08_11-48-24_feedback_stable_20261008_v2init", "logs/background/agilekickball_v3_feedback_stable_20261008_114819.log", "logs/background/agilekickball_v3_feedback_stable_20261008_114819.pid", "logs/rsl_rl/agilekickball_v3_smoke/2026-10-08_11-41-58_feedback_stable_scale_smoke"]
task_contract_sha256: "f01896049457022c72b78f95be5c86a9740858f53ed4d4b07c20b1cc57843b05"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_state_feedback.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "8a64957c8c0dbaa892b025807418a3d94725b313191624ba19ab65e0dc9d6912", "stdout_sha256": "8b927efc8a89aac73059b2118142b897a7b88c139ca4af262e433663c2751903", "stderr_sha256": "a1490b725d6505bab59ca1bb9746cc84e3ce19ba95736e81974babc9c88af695", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "2c2cdedcfd922b65a901ff9fbcdfea89ab151033175e669e47945355a8beed98", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "40a7c83430b33b71e474d48e5d4ce919084def0f3ad38a8ca98453e3cced4c0e", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v3.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "1d62a83bc8ed2afddb0ddf08e9ab2de07b15492cd74d08f81223147e2124831e", "stdout_sha256": "0ff0c1780e86161b765f8f0bb42944acaa41a6d6e3f8157293b611b0f73d3284", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

已完成故障诊断、v3 稳定性配置修复、真实恢复验证，并按用户授权重新启动后台正式训练。当前 revision feedback_stable_20261008，PID 1776883，4096 环境、cuda:0、50000 轮、seed 42。启动核验已到日志第 67 轮（0 起编号）。DONE 指修复和启动完成，不表示长期训练已经收敛。

失败 run 的 50000 轮恢复数始终为零，最后 1000 轮 episode 58.81 控制步即 1.176 s；实际物理配置与 v2 一致。64 环境各 1500 步、相同 0.4–2 m/s / 1.3–2 m 回放，v2 恢复 855 次，失败 v3 为 0，关闭残差也为 0；采样策略分别 567 与 0。失败主策略本身失稳，不能通过仅关闭残差、降低探索噪声或放宽恢复规则解释/修复。

512 个真实状态中，三个位置 raw logstd 全部处于旧硬截断以下；精度权重约 2981，NLL 对 encoder 梯度范数为同尺度半归一化 MSE 的 1368.6 倍，一步旧 Adam 辅助更新未回退 KL 约 0.0296。它证明硬截断饱和及强梯度共享路径的存在，不是唯一根因的单因素因果证明。旧辅助已接受 199767/200000 个批，不是没有训练。详细审计、配置差异、回放和梯度证据在本次目录。

修复配置：NLL 仅更新预测头、输入特征 detach，主 encoder 仍由 PPO 学习；平滑 logstd [-2,1]；辅助 lr 1e-4、完整动作 KL 上限 .001、残差最大 .1 raw 即 .025 rad。参数进入 typed config 和 schema2 checkpoint。显式从已收敛 v2 迁移主 actor/encoder/critic 与归一化/std/AMP；新头、残差、三个优化器和轮数重新初始化。新课程 E=60000，距离 1.3–2 m、速度 .4–1.1 m/s，扩展未解锁。任务奖励、几何、恢复阈值和课程推进规则不变。

首次真实 smoke 发现 v2 迁移后用从零训练的 PPO 初始 lr .001 会在更新后破坏恢复，因此在允许的 v3 稳定性配置组内将 PPO 初始 lr 降到 1e-5，保留原 adaptive KL 调度、PPO 算法和其余参数。第二次完整启动发现写 initialization.json 前日志目录尚未创建，已显式创建。两次范围内修复后冻结命令全 PASS，失败 receipts/log 单独保存，未放宽恢复断言。

12 项模块测试、159 项任务/legacy 回归通过，覆盖初始化动作/critic 逐元素一致、AMP 迁移、独立辅助梯度、完整参数/Adam 回退、平滑有界方差、非零残差 TorchScript/ONNX、schema/恢复兼容。16 环境各 1000 步真实恢复：迁移后 98 次，更新和续训后 92 次，无倒地终止。4096 环境正式 PPO 参数 100 轮短训通过，末轮 episode 约 30.16 s；辅助主encoder更新数0，预测头每轮4批，全部有限。100 轮后同条件 64 环境回放恢复 900 次、走出边界终止12次、无倒地；它继承 v2 权重，不能当作新增反馈机制优于 v2 的证据。

正式进程核验：独立 session/PID、实际 CLI 与 saved agent.yaml、首个有限 checkpoint、schema2、warm-start 来源与 SHA256、辅助 optimizer 均正常。第 67 轮日志 episode 均值 25.82 s，恢复发球累计指标 34947.67（rollout 平均值，不是单次窗口的整数计数）；预测头接受 4/4 批，NLL encoder 更新0，完整辅助阶段 KL 1.8574109e-11。没有 NaN/OOM/Traceback。

日志：/home/cao/perceptual_ball/logs/background/agilekickball_v3_feedback_stable_20261008_114819.log
模型目录：/home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v3/2026-10-08_11-48-24_feedback_stable_20261008_v2init
启动命令：bash scripts/rsl_rl/train_agilekickball_v3.sh。当前已运行，勿重复启动。

限制：新训练是 v2 权重初始化而非 scratch；后续论文须显式计算预训练预算、固定评测分布并做多种子/消融。平滑方差未校准、短测不是长期收敛证明。旧模型、日志、反馈/Outcome 归档任务保留；v2 和共享物理/PPO源码哈希与此前快照一致。51 个训练源文件及 SHA256 已归档。
