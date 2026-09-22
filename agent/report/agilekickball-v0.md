---
task_id: "ENG-AGILEKICKBALL-V0-20260920"
status: "PARTIAL"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/curriculums.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball.py", "tests/test_agilekickball.py", "scripts/rsl_rl/smoke_agilekickball.py", "scripts/rsl_rl/smoke_agilekickball.sh", "docs/agilekickball/README.md", "docs/agilekickball/test_receipts.json", "docs/agilekickball/artifact_validation.json", "docs/agilekickball/validation/smoke.log", "docs/agilekickball/validation/recovery_diagnostics.md", "docs/agilekickball/validation/smoke_model.pt", "agent/plan/agilekickball-v0.md", "agent/task/agilekickball-v0.md", "agent/report/agilekickball-v0.md", "agent/handoff/agilekickball-v0.md"]
task_contract_sha256: "e0009bc5fd5371630128788e6ebc5a230fecc0276e77406b90ce5bf05ed24903"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "13d3b7031c97301d82ae75a11c57184215889070fb07218079dae948071de702", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "32530a01f9c08a4a138d32af43b2a75edeec9c857d7e2a4e3ab966155a4634a0", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball.sh", "result": "FAIL", "exit_code": 1, "executed": true, "receipt_sha256": "efe468104f497b184b60ab479c0f2914d128889428b1d6ea9cb59f1c0ec4e57f", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "bd8f6b0fe2db286035751c55333c5908657fa2688908703b4052dd5730eba392", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

# AgileKickball 实现与验证状态

已新增独立 Template-Perceptual-Ball-AgileKickball-v0，继承当前v0奖励、观测、网络与PPO；增加来球速度上限0.8→2.0m/s的240000控制步课程。根据用户追加要求，新增恢复后连续发球：默认站姿reset、RSI=0、先等连续稳定0.3秒和最小等待0.4秒，球结束后不reset机器人，恢复后发下一球；等待满5秒仍未发球时终止。episode延长至60秒。原v0、v2、v3配置未修改。

7项CPU测试PASS：课程边界、环境数量独立性、恢复进度、错误参数、首次/第二次发球、连续稳定中断、倒立防护、部分reset、超时和termination优先级、不重复推进，以及球回合不写robot状态。真实仿真能创建环境和执行reset/step，但smoke FAIL：零动作、简单测试用踝反馈和现有v0策略均不能维持新增恢复条件，尚未达到同episode第二次发球验收。保留严格断言与失败回执，未改变姿态阈值、施加外力、固定机器人或伪造发球计数。

因此状态PARTIAL，不能宣称真实连续发球已验证、策略已学会恢复或任务整体验收完成。代码入口和训练命令已提供；进一步验证需要能完成恢复的策略。详见docs/agilekickball/README.md和validation/recovery_diagnostics.md。本轮未启动长期训练，旧checkpoint和参考数据只读。最终版本在连续发球断言处停止，不能声称其PPO/checkpoint smoke通过。
