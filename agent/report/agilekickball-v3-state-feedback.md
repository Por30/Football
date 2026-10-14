---
task_id: "AGILE-V3-STATE-FEEDBACK-20261006"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/state_feedback.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/export.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_outcome_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3_outcome.py", "tests/test_state_feedback.py", "tests/test_agilekickball_v3.py", "tests/test_agilekickball_v3_outcome.py", "tests/test_contact_outcome.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "scripts/rsl_rl/train_agilekickball_v3.sh", "docs/agilekickball_v3/README.md", "docs/agilekickball_v3/state_feedback_20261006", "README.md", "agent/plan/agilekickball-v3-state-feedback.md", "agent/task/agilekickball-v3-state-feedback.md", "agent/report/agilekickball-v3-state-feedback.md", "agent/handoff/agilekickball-v3-state-feedback.md", "logs/rsl_rl/agilekickball_v3/2026-10-06_13-17-10_state_feedback_20261006_scratch", "logs/background/agilekickball_v3_state_feedback_20261006_131706.log", "logs/background/agilekickball_v3_state_feedback_20261006_131706.pid", "logs/rsl_rl/agilekickball_v3_smoke/2026-10-06_13-16-16_state_feedback_scale_smoke"]
task_contract_sha256: "b56f1a916a4ddc9a2e2ec2b44965a0021f24b8c34b0f81179faea4e6174cda2f"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_state_feedback.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "8a64957c8c0dbaa892b025807418a3d94725b313191624ba19ab65e0dc9d6912", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "0c74eb2ba93ebe433dfd497906a96e44fda6259f40fb64f0ed7b74a4a2af7fc3", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "2c2cdedcfd922b65a901ff9fbcdfea89ab151033175e669e47945355a8beed98", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "23ac37891e89e2679e54253d760b2ea090dbd42d62eb4c2d0c8f832ed62d11d4", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v3.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "1d62a83bc8ed2afddb0ddf08e9ab2de07b15492cd74d08f81223147e2124831e", "stdout_sha256": "f22a7d05dbb944e86d062c5b2823ee16c52ffbdf0cede9cffd4720bd326051b0", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

基于 v2 完成新 v3（state_feedback_20261006），并按授权启动后台正式 scratch 训练。PID 1499582，4096 环境、cuda:0、50000 迭代、seed 42；检查时已到第 11 轮（日志从 0 编号）。独立 session、进程启动时间、实际参数和有限 checkpoint 已核实。DONE 指实现、验证和启动完成，不表示 50000 轮已经训练结束。

新方法融合深度与本体历史，预测当前球的位置/速度均值和标准差，使用可见性/不确定性门控的有界动作修正；原主 actor 保留，修正末层零初始化。PPO 学习动作，NLL 训练编码器/预测头，预测值在动作分支 detach。旧未来后果辅助移到 Outcome 归档任务。物理场景、课程、奖励、PPO、AMP、恢复规则与 v2 相同：最终距离 1.3–2 m，横向 ±0.25 m，机器人活动半径 0.6 m，球速最高 6 m/s。恢复 v2 难度是本轮比较设计选择；旧 3 m / ±0.35 m / 1.2 m 保留在 legacy。

9 项新模块测试和 158 项任务/legacy 回归通过。真实 CPU 仿真通过两次 scratch 更新和一次续训、课程冻结、边界、Adam 精确恢复、旧最终 checkpoint 加载；正式 4096 环境/24 步/5 epoch/4 minibatch GPU 短测通过，4 批辅助更新全部接受，stage KL 0.00071015873。新分支非零输出的 TorchScript/ONNX 一致性通过。冻结 smoke 前两次失败均为验证脚本字段读取接口差异（配置默认 KL、v2 默认 aim），两次范围内修正后通过，保留失败 receipts/log；没有放松实际 KL/几何断言或修改训练代码。

正式进程最近记录辅助接受批数 4/4、累计接受 48，阶段 KL 0.00067552051，修正平均绝对值 0.0070958678 raw action。首个 checkpoint 包含新课程、辅助配置、计数和 Adam，模型及记录标量有限。证据在 docs/agilekickball_v3/state_feedback_20261006/；49 个训练源码文件另外快照保存。

正式日志：/home/cao/perceptual_ball/logs/background/agilekickball_v3_state_feedback_20261006_131706.log
模型目录：/home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v3/2026-10-06_13-17-10_state_feedback_20261006_scratch
启动入口：bash scripts/rsl_rl/train_agilekickball_v3.sh。当前实例运行中，不应重复启动。

效果尚未验证优于 v2。NLL/预测误差来自训练集，门控标准差未校准，合成球深度可见性不是通用实拍检测器；有限样本辅助 KL 不保证全状态稳定。后续需固定评测分布和交互预算、多种子，并拆分 NLL/本体融合/门控/残差的消融。旧日志模型未覆盖，v2 代码未改变；开始前工作区已有的无关修改保留。
