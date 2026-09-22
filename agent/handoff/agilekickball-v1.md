---
task_id: "ENG-AGILE-V1-20260921"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "HANDOFF"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_state.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v1.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v1_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/smoke_agilekickball_v1.py", "scripts/rsl_rl/smoke_agilekickball_v1.sh", "tests/test_agilekickball_v1.py", "docs/agilekickball_v1/README.md", "docs/agilekickball_v1/test_receipts_attempt1.json", "docs/agilekickball_v1/test_receipts.json", "docs/agilekickball_v1/validation/smoke_model.pt", "docs/agilekickball_v1/validation/smoke.log", "docs/agilekickball_v1/validation/diagnostics.md", "docs/agilekickball_v1/validation/smoke.json", "agent/plan/agilekickball-v1.md", "agent/task/agilekickball-v1.md", "agent/report/agilekickball-v1.md", "agent/handoff/agilekickball-v1.md"]
task_contract_sha256: "d316655981c3af6e982493f3c5b9eb795f85b3b118c6361a830ea542c2aec2c2"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v1.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "b4b60dbc7e19b021e8aa3c779067db6a2cf08505ea94fdb559dd07717aa08855", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "a8e26f4d9de3d13eed0b80eab9cd14a2e06c705aa77040f28baa36bf90a529ae", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v1.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "16c1118b590fe835280148e6f58681b05f8ce54124562e7c2dd440ed1b0c9ebb", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
---

v1实现和验证完成，两个冻结命令最终PASS。直接运行docs/agilekickball_v1/README.md中的命令，从v0 model_25200初始化新v1；优化器/网络继承，课程从stage0开始，50000为额外迭代预算。不会改动旧checkpoint。

保持v0接口默认行为；共享改动仅抽速度采样与恢复ready helper，runner按v1课程接口分派。v1._serve必须先结算旧球再采样，晋级只在tick尾执行。round_stage/challenge标签不随课程变化。播放load_optimizer=False不加载优化器并冻结课程统计；load后显式reset才能建立第一颗计数球。旧在途球不能从无物理快照checkpoint恢复。

若后续修改课程阈值或采样合同，checkpoint配置校验会拒绝直接续训，需另行明确迁移。未经讨论不要把构造stage9 smoke作为达到5m/s成功率证据；严格成功仍是运动学代理。已有近脚感知盲区与v0宽松奖励保持原状，需要独立任务处理。原始验证在docs/agilekickball_v1/validation/smoke.json，命令、口径和限制在README。
