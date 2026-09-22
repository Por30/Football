---
task_id: "ENG-AGILE-LEARNING-20260920"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "REPORT"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_state.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_env_cfg.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/algorithm.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/ball_metrics.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "tests/test_agilekickball.py", "tests/test_agilekickball_learning.py", "scripts/rsl_rl/validate_agilekickball_learning.py", "scripts/rsl_rl/validate_agilekickball_learning.sh", "docs/agilekickball/README.md", "docs/agilekickball/learning_test_receipts.json", "docs/agilekickball/learning_test_receipts_attempt1.json", "docs/agilekickball/learning_test_receipts_attempt2.json", "docs/agilekickball/learning_validation/diagnostics.md", "docs/agilekickball/learning_validation/result.json", "docs/agilekickball/learning_validation/run.log", "docs/agilekickball/learning_validation/model_validation.pt", "agent/plan/agilekickball-learning-fix.md", "agent/task/agilekickball-learning-fix.md", "agent/report/agilekickball-learning-fix.md", "agent/handoff/agilekickball-learning-fix.md"]
task_contract_sha256: "db025a4b23900dc0eef675f51e808339acbd5570fc5df8d78e49685427adb4e3"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_learning.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "8fb13d8d12f713345c0df3400afa386d2033a028bc1e4ba6731740b52dd216d4", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "f6bb65b1212adfd9794a4eb8d95ab7d941dd30f481757cf2fe2071c7210a2635", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/validate_agilekickball_learning.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "be8376f8f090a96fd9e88fde0a539d9aa25591124dd140f2a9f2b376e79178d8", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
---

工程修复及监督评估完成，未声称策略已学会连续恢复击球。

修复首个辅助更新被KL拒绝即误报loss=0；所有rollout样本独立统计位置/速度向量RMSE、P95及活动/可见/来球/近脚分层。Agile辅助更新增加最多7次回溯及head-only fallback、累计actor KL监测，维持v0网络和奖励。

episode reset立即发第一颗运动中的球，移除2.5m静止覆盖；局内保持0.3s连续稳定、0.4s冷却和5s超时。0.5–0.7m初期近距离物理来球逐渐恢复原距离，课程只计按环境数归一化的真实来球曝光，新checkpoint保存恢复计数。

23项CPU回归和16环境/32轮真实PPO更新通过。固定留出集活动可见972/1536样本的位置RMSE 77.67→19.72cm，速度0.680→0.227m/s；旧checkpoint同集为92.54cm/0.544m/s，仅只读对照。近脚位置65.91→34.11cm，速度0.530→0.541m/s，尚未改善。新种子活动可见集18.66cm/0.256m/s。128次编码器更新，训练来球比例平均96.39%、每轮最低91.15%，近脚1060/12288。独立评估不更新网络/归一化。

物理短跑累计初始发球673、恢复后发球0；边界测试验证同episode第二球、不重置robot、连续稳定和超时优先，但未证明学习策略自然通过恢复门控。没有深度打乱/常量预测基线，监督改善不单独证明充分使用视觉。未测4096吞吐、最终高速课程、真机或训练收敛。旧训练PID2487905未停止，需重新启动进程才载入新代码。训练命令及解释见docs/agilekickball/README.md。

前两次集成失败分别为startup前观测探测缺少状态、验证脚本inference缓存上下文不一致；做两次根因修复，未削弱覆盖/误差断言。最终回执两个命令均PASS，历史attempt回执保留。
