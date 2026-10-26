---
task_id: "agilekickball-v11-20261025"
language: "zh-CN"
axes: ["L", "P", "D", "C"]
risk_tier: "T2"
status: "DONE"
changed_files: ["agent/handoff/agilekickball-v11-20261025.md", "agent/plan/agilekickball-v11-20261025.md", "agent/report/agilekickball-v11-20261025.md", "agent/task/agilekickball-v11-20261025.md", "docs/kickball_v11/README.md", "docs/kickball_v11/artifacts_validation.json", "docs/kickball_v11/cpu.log", "docs/kickball_v11/cpu_attempt1.log", "docs/kickball_v11/cpu_attempt2.log", "docs/kickball_v11/exported/manifest.json", "docs/kickball_v11/exported/policy.onnx", "docs/kickball_v11/exported/policy.pt", "docs/kickball_v11/incompatible_model.pt", "docs/kickball_v11/receipts.json", "docs/kickball_v11/receipts_attempt1.json", "docs/kickball_v11/receipts_attempt2.json", "docs/kickball_v11/smoke.json", "docs/kickball_v11/smoke.log", "docs/kickball_v11/smoke.py", "docs/kickball_v11/smoke_attempt1.log", "docs/kickball_v11/smoke_attempt2.log", "docs/kickball_v11/smoke_model.pt", "docs/kickball_v11/source_identity.json", "docs/kickball_v11/validate_cpu.sh", "docs/kickball_v11/validate_sim.sh", "projects/README.md", "projects/football/README.md", "scripts/rsl_rl/play.py", "scripts/rsl_rl/play_kickball_v11.sh", "scripts/rsl_rl/train.py", "scripts/rsl_rl/train_kickball_v11.sh", "source/perceptual_ball/perceptual_ball/kickball_v11.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/kickball_v11.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/kickball_v11_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_v11.py", "tests/test_kickball_v11.py"]
task_contract_sha256: "2850313b17a5699af8109f77f4dd6978797499be7f9cd7badb3d566ad0b01e0c"
tests: [{"command": "bash docs/kickball_v11/validate_cpu.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "af3af618d427c2ab0f184de75fb731796c01f40bb745202bf992688a47e9351b", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/kickball_v11/validate_sim.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "03850c36c411bf1f482ca75c0aa07c5fb519fae48cc84fd2d92e8b25f1f4be81", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

已完成独立Kickball-v11：无墙柱/箱体，保持wall11控制与带噪历史观测，v4连续回传最高5m/s，全站姿reset。Actor558＋4×27×48，独立critic124；球状态辅助头监督CNN，预测与真值均不作为额外actor输入。AMP采用原左右脚数据的60×10特征、原命名末端与零球槽。

共享生产改动仅为wall10默认关闭的辅助损失hook、新任务注册和train/play分支。215项CPU及16环境2＋1轮联合更新、严格恢复课程、终止/partial-reset隔离、真实球深度、JIT/ONNX导出通过，回执位于docs/kickball_v11/receipts.json。修复root-link重置速度缓存及恢复重置inference-mode问题；失败证据保留。

状态为实现与短测完成，未启动正式训练或评估成功率，未验证4096吞吐、sim2sim或实机。正式命令：bash scripts/rsl_rl/train_kickball_v11.sh；产物进入logs/rsl_rl/agilekickball_v4/kickballv11/。启动前重新只读核对进程和GPU。播放命令：bash scripts/rsl_rl/play_kickball_v11.sh /绝对路径/model_500.pt 4。

工程恢复不需要后续命令；用户若开始训练必须使用新模型或同版本resume。模型/优化器课程契约拒绝旧wall11/v4；既有足球/搬箱数据、模型与任务行为保留。工作区同期wall12文件不属于本任务。详见docs/kickball_v11/README.md及smoke.json。