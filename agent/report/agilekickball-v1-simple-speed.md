---
task_id: "ENG-AGILE-V1-SIMPLE-SPEED-20260922"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
status: "DONE"
changed_files: ["agent/handoff/agilekickball-v1-simple-speed.md", "agent/plan/agilekickball-v1-simple-speed.md", "agent/report/agilekickball-v1-simple-speed.md", "agent/task/agilekickball-v1-simple-speed.md", "docs/agilekickball_v1/README.md", "docs/agilekickball_v1/simple_speed_validation/course_smoke_model.pt", "docs/agilekickball_v1/simple_speed_validation/metadata.json", "docs/agilekickball_v1/simple_speed_validation/receipts.json", "docs/agilekickball_v1/simple_speed_validation/scratch_smoke_model.pt", "docs/agilekickball_v1/simple_speed_validation/smoke.json", "docs/agilekickball_v1/simple_speed_validation/smoke.log", "docs/agilekickball_v1/simple_speed_validation/summary.md", "docs/agilekickball_v1/strict_curriculum_archive_20260922/README.md", "docs/agilekickball_v1/strict_curriculum_archive_20260922/agilekickball_v1.py", "docs/agilekickball_v1/strict_curriculum_archive_20260922/agilekickball_v1_env_cfg.py", "docs/agilekickball_v1/strict_curriculum_archive_20260922/runner.py", "docs/agilekickball_v1/strict_curriculum_archive_20260922/smoke_agilekickball_v1.py", "docs/agilekickball_v1/strict_curriculum_archive_20260922/smoke_agilekickball_v1.sh", "docs/agilekickball_v1/strict_curriculum_archive_20260922/test_agilekickball_v1.py", "docs/agilekickball_v1/strict_curriculum_archive_20260922/test_play_ballspeed.py", "scripts/rsl_rl/smoke_agilekickball_v1.py", "scripts/rsl_rl/smoke_agilekickball_v1.sh", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v1_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v1.py", "tests/test_agilekickball_v1.py", "tests/test_play_ballspeed.py"]
task_contract_sha256: "51b06adbb56615d0a9a73a9bb31a8c8862e7ff91b11948f33af7d0c2f13c6a08"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v1.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "b4b60dbc7e19b021e8aa3c779067db6a2cf08505ea94fdb559dd07717aa08855", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "525149fc5c73ed6b7af810c5fd43d05f00682bd6813ce5d9aa5d59d882ec00b3", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_play_ballspeed.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "706000957b18913f54c8db837ba8dd5bceada41f373d56fb7ec984b52ac133e8", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "ada1202e99bc51260c4ec87f807f20c9c6ee83b3b2dc72a56554ad1281054d3e", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v1.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "16c1118b590fe835280148e6f58681b05f8ce54124562e7c2dd440ed1b0c9ebb", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

已按用户要求重建 v1 为基于 v0 的简单渐进速度课程。前240000有效来球平均步保持v0上限0.8→2.0，再240000步2.0→5.0；恢复原近距离bootstrap。取消strict成功窗口/挑战混合，仅用统一均匀采样。等待恢复不推进，环境数量不加速课程。v0源文件hash未变；真实配置检查确认观测、奖励、动作、终止、网络与PPO一致。

v1仅移除all-joint瞬时RMS门槛，保留关节有限值检查、全部身体/脚位条件、连续0.3s、0.4s冷却、5s超时、终止优先及局内只reset球。checkpoint schema2使用新key，合法v0可迁移曝光；旧strict checkpoint显式拒绝，不能混用。Play冻结课程，ballspeed覆盖包含恢复后发球且不持久化。

三条冻结验收全部通过，包含继承的v0/学习回归、课程边界/均值/reset/tick/非有限值、真实Isaac CPU 16环境新初始化策略1次PPO更新（64/64 incoming样本，1次encoder更新，损失有限）、实际采样最高4.924m/s、checkpoint冻结和固定速度覆盖。

同一个旧model_30600停站策略、相同0.4–0.8m/s和1.3–2m、随机动作、16环境1000步（20s）对照：原关节门控0次恢复发球/24次episode终止，新身体门控39次恢复发球/0次终止。旧等待joint RMS均值1.731rad/s、joint gate通过31.25%、身体条件通过93.57%、最长连续稳定0.16s；新为1.706rad/s、32.73%、92.39%、0.38s。对照支持恢复门槛修复，不代表所有故障都来自joint RMS，也不代表该旧策略获得主动踢球能力。

未启动长训练、未终止用户进程、未使用真实硬件。没有5m/s能力或长期收敛结论；50000轮是否达到5m/s取决于实际来球曝光（30%来球比例约到3.5m/s）。从零启动命令与解释见docs/agilekickball_v1/README.md。旧源码/测试/smoke/说明快照在strict_curriculum_archive_20260922，旧validation和audit保留作为历史，不是新版本验收。

