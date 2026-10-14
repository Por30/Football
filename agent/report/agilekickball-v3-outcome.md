---
task_id: "AGILE-V3-OUTCOME-20261003"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/contact_outcome.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "tests/test_contact_outcome.py", "tests/test_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "scripts/rsl_rl/train_agilekickball_v3.sh", "docs/agilekickball_v3/README.md", "README.md", "agent/plan/agilekickball-v3-outcome.md", "agent/task/agilekickball-v3-outcome.md", "agent/report/agilekickball-v3-outcome.md", "agent/handoff/agilekickball-v3-outcome.md", "docs/agilekickball_v3/outcome_20261003/receipts.json", "docs/agilekickball_v3/outcome_20261003/smoke.json", "docs/agilekickball_v3/outcome_20261003/scale_smoke.json", "docs/agilekickball_v3/outcome_20261003/artifacts.json"]
task_contract_sha256: "de4540187e4b1e004818468d730f6eb80aff450f0a054300b25bdd5773c28637"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_contact_outcome.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "ebc452bf6ef4682ef1ef5e33c5df62def4be280ba7e322577cf114ac2c5b4363", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "b60527577bf5fb3e9096ac886240aa640e47779b31142e667b9e25fddf137679", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "2c2cdedcfd922b65a901ff9fbcdfea89ab151033175e669e47945355a8beed98", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "08ecbab12305b688f3483bad12ddf4a60c20bad35b6e4600d8ed2b39467019c6", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v3.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "1d62a83bc8ed2afddb0ddf08e9ab2de07b15492cd74d08f81223147e2124831e", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

在现有 v3 空间课程上实现训练期短时后果辅助，v2 保持原行为。当前版本 contact_outcome_20261003，从零训练，最远 3 m、横向终点 ±0.35 m、机器人活动半径 1.2 m。共享原 CNN，以 actor 特征和当前动作预测 8 步后球速度、gravity XY、root height 及窗口 kick proxy；不增加部署输入，不生成参考轨迹。

11 个专项测试及继承 v2/v1 回归通过。真实 CPU 仿真完成两次 scratch PPO 更新、课程冻结/空间边界验证及一次恢复更新，outcome Adam 状态逐元素一致。正式启动脚本通过 16 环境两次 GPU 更新；额外生产规模 4096 环境/24 步/5 epoch/4 minibatch 一次更新正常退出：62685 有效窗口、抽样 8192、4 批编码器更新，阶段 KL 3.18253e-5。规模检查记录见 scale_smoke.json，不作为长期训练性能结论。

首次专项测试发现重载 Adam state_dict 会复用快照 tensor，使重试污染快照；已通过逐次深拷贝修复，精确动量恢复测试通过。标签严格排除重置/再发球及尾部窗口，训练计数用 float64。辅助 stage KL 超限先回退减小学习率，再只更新预测头。保存与加载检查新增配置和 optimizer，旧 revision 在模型变更前拒绝。

正式命令：cd /home/cao/perceptual_ball 后运行 bash scripts/rsl_rl/train_agilekickball_v3.sh。默认 4096 环境、cuda:0、50000 迭代、seed 42。关闭辅助对照增加 agent.algorithm.outcome_aux_coef=0.0 并设置独立 run_name。

限制：未启动正式长训；没有证明比 v2 更好。预测对象是随后 rollout 策略下的短时统计结果，不是反事实世界模型或恢复成功率。kick proxy 不是真实接触真值；跨终止的未来窗口被排除，不能用于跌倒风险主张。仅支持单 GPU。原始 v2 与 v3 空间分布不同，应使用同空间的 outcome-off 检验辅助。历史记录保留于原目录，改动前文件另有 before 快照。
