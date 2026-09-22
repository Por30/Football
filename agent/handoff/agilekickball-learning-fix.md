---
task_id: "ENG-AGILE-LEARNING-20260920"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "HANDOFF"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_state.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_env_cfg.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/algorithm.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/ball_metrics.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "tests/test_agilekickball.py", "tests/test_agilekickball_learning.py", "scripts/rsl_rl/validate_agilekickball_learning.py", "scripts/rsl_rl/validate_agilekickball_learning.sh", "docs/agilekickball/README.md", "docs/agilekickball/learning_test_receipts.json", "docs/agilekickball/learning_test_receipts_attempt1.json", "docs/agilekickball/learning_test_receipts_attempt2.json", "docs/agilekickball/learning_validation/diagnostics.md", "docs/agilekickball/learning_validation/result.json", "docs/agilekickball/learning_validation/run.log", "docs/agilekickball/learning_validation/model_validation.pt", "agent/plan/agilekickball-learning-fix.md", "agent/task/agilekickball-learning-fix.md", "agent/report/agilekickball-learning-fix.md", "agent/handoff/agilekickball-learning-fix.md"]
task_contract_sha256: "db025a4b23900dc0eef675f51e808339acbd5570fc5df8d78e49685427adb4e3"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_learning.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "8fb13d8d12f713345c0df3400afa386d2033a028bc1e4ba6731740b52dd216d4", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "f6bb65b1212adfd9794a4eb8d95ab7d941dd30f481757cf2fe2071c7210a2635", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/validate_agilekickball_learning.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "be8376f8f090a96fd9e88fde0a539d9aa25591124dd140f2a9f2b376e79178d8", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
---

当前稳定状态：工程修复和短跑评估已完成，两条冻结命令最终PASS。完整定义、数值、启动命令见docs/agilekickball/README.md；原始数据learning_validation/result.json。

后续按用户训练计划启动4096环境/50000轮新run learning_fix；本次只完成16环境32轮短训练。旧进程PID2487905仍使用旧代码，未自动终止或替换其checkpoint。新进程不自动加载短跑或旧模型。

必须保持首球引导与局内恢复分支分离，不允许因暂未学会恢复而降低连续稳定门槛。aux拒绝不能伪造零误差，head-only必须encoder.grad=None。可见判据仅适用当前无噪声合成深度。active/visible/near标签来自动作前rollout，不读取当前环境给过去样本打标签。

局限：真实学习策略recovered_serves仍为0，尚未完成连续击球性能验证；近脚速度误差未改善，速度是世界线速度在root轴下表达。不可将673次初始发球或15次v0成功代理当作稳定连续回球。课程曝光checkpoint已roundtrip；旧checkpoint无进度时从0起。历史validation/smoke失败记录为旧门控方案，当前验证入口是validate_agilekickball_learning.sh。
