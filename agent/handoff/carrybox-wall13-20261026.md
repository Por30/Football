---
task_id: "carrybox-wall13-20261026"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall13-20261026.md", "agent/plan/carrybox-wall13-20261026.md", "agent/report/carrybox-wall13-20261026.md", "agent/task/carrybox-wall13-20261026.md", "docs/carrybox/wall13_20261026/README.md", "docs/carrybox/wall13_20261026/artifact_validation.json", "docs/carrybox/wall13_20261026/final_state.json", "docs/carrybox/wall13_20261026/receipts.json", "docs/carrybox/wall13_20261026/smoke.json", "docs/carrybox/wall13_20261026/smoke.log", "docs/carrybox/wall13_20261026/smoke.py", "docs/carrybox/wall13_20261026/smoke_model.pt", "docs/carrybox/wall13_20261026/validate.sh", "projects/README.md", "projects/findbox/README.md", "scripts/rsl_rl/play_carrybox_walled.sh", "scripts/rsl_rl/train_carrybox_walled.sh", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall13_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall13.py"]
task_contract_sha256: "9f2bb3f18707a809febb60f126d74137e1e6b38cf05cb00bddfbba18e2a35ae1"
tests: [{"command": "bash docs/carrybox/wall13_20261026/validate.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "bebb75c16d8dddfc278aebdd1d3b980f0ff3837f7afc1cb6982c720863f56989", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

wall13实现和16环境定向更新/恢复检查完成。数据选择明确是assets/motions/findbox revision3 findbox_hold_v1_named，与wall12 model19999已使用的数据相同；用户若提供另一个修改版路径，须核对数据/schema/哈希后再换AMP路径，不改RSI或其他训练配置，不伪称已做不同数据对照。

复用CarryBoxWall12OnPolicyRunner/PPO，aux1.0、4096x24、5x4保持。正式命令：CARRYBOX_VARIANT=13 bash scripts/rsl_rl/train_carrybox_walled.sh（本次未执行）。回放使用CARRYBOX_VARIANT=13 bash scripts/rsl_rl/play_carrybox_walled.sh <wall13_checkpoint> 4。wall12旧模型不能严格恢复到wall13。验证复跑：bash docs/carrybox/wall13_20261026/validate.sh。

不改旧数据/manifest/映射及工作区已有评估文档。检查时足球PID3814037运行，未停止任何进程。证据及训练/回放命令见docs/carrybox/wall13_20261026/README.md；当前无wall13正式训练，也无成功率结论。
