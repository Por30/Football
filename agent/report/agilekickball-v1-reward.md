---
task_id: "ENG-AGILE-V1-REWARD-20260922"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["agent/handoff/agilekickball-v1-reward.md", "agent/plan/agilekickball-v1-reward.md", "agent/report/agilekickball-v1-reward.md", "agent/task/agilekickball-v1-reward.md", "docs/agilekickball_v1/README.md", "docs/agilekickball_v1/reward_validation/before/README.md", "docs/agilekickball_v1/reward_validation/before/agilekickball_v1_env_cfg.py", "docs/agilekickball_v1/reward_validation/before/rewards.py", "docs/agilekickball_v1/reward_validation/before/smoke_agilekickball_v1.py", "docs/agilekickball_v1/reward_validation/before/smoke_agilekickball_v1.sh", "docs/agilekickball_v1/reward_validation/course_smoke_model.pt", "docs/agilekickball_v1/reward_validation/receipts.json", "docs/agilekickball_v1/reward_validation/scratch_smoke_model.pt", "docs/agilekickball_v1/reward_validation/smoke.json", "docs/agilekickball_v1/reward_validation/smoke.log", "docs/agilekickball_v1/reward_validation/summary.md", "docs/agilekickball_v1/reward_validation/unchanged_hashes.json", "scripts/rsl_rl/smoke_agilekickball_v1.py", "scripts/rsl_rl/smoke_agilekickball_v1.sh", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v1_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/rewards.py", "tests/test_agilekickball_rewards.py"]
task_contract_sha256: "b9908cc00f2120f0830074d568badfdb2b9b6246b1a35b653689b0c0359e2a45"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_rewards.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "6dcd4345d45cca7664f6de8b5927002fb76932b7888858dc5f3a37c5f9b5760e", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "d8bca44dbe93f046a4333e65ede715d6273bcf9b8bf455b533c6fa75e4b5f40c", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v1.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "b4b60dbc7e19b021e8aa3c779067db6a2cf08505ea94fdb559dd07717aa08855", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "70ade7fd70f46d3ca207f0577b3192bb3546d031a6ae52e5c395d57bd2dbc576", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v1.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "16c1118b590fe835280148e6f58681b05f8ce54124562e7c2dd440ed1b0c9ebb", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

在简单速度v1基础上，仅增强奖励偏好。踢球事件60→300（5倍），回球速度4→8（2倍），漏球−15→−60（4倍），面向球0.5→0.2。来球活跃且未踢出时原站立奖励乘0.25，踢出后/恢复时为1。接近项仍1.2，避免放大球自己接近带来的收益。其余正则项不变。

控制周期0.02s：单次踢球任务奖励1.2→6，漏球−0.3→−1.2；AMP混合后任务部分分别为4.5和−0.9。kickball_tick仍非零；事件pulse的原一次性、恢复门控与终止优先没有改变。Shared rewards.py仅增加函数，原函数AST一致；v0配置、v1课程/状态类hash一致；真实配置检查确认网络/PPO/AMP/观测/终止/动作不变。

三个冻结命令通过：奖励4项边界测试、现有v1/v0/学习回归，Isaac CPU16环境从零策略1次PPO更新（64/64 incoming、1次encoder更新，所有loss有限），checkpoint/play/速度端点与恢复回归。旧smoke要求奖励完全等同v0已被用户此次新需求取代，改为明确检查新权重及其他项不变；修改前源码与smoke保存在reward_validation/before。

新增真实物理奖励排序：相同0.4–0.8m/s、1.3–2m、seed922，16环境1000步，每个策略均用deterministic动作。记录为新任务环境奖励（包含原正则，未混AMP），不是新策略收敛对照：

- standing：每环境每步任务奖励 0.011904，kick proxy 0，恢复发球 48，episode终止 0。
- kicking：每环境每步任务奖励 0.055488，kick proxy 77，恢复发球 88，episode终止 0。

以上只说明当前奖励在这两份已有策略上更偏好踢球，不证明所有策略或完整AMP混合目标都具有相同排序，也不证明从零训练消除站立局部最优。kick proxy仍可能包含被动反弹，本次不增加严格成功条件。未启动长期训练、未操纵用户已有进程、未修改真实设备。运行中的进程不会自动应用新奖励；从零重新启动，训练命令见README，run_name=v0_gradual_speed_kick_reward_scratch。

