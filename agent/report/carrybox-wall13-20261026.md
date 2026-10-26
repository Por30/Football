---
task_id: "carrybox-wall13-20261026"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall13-20261026.md", "agent/plan/carrybox-wall13-20261026.md", "agent/report/carrybox-wall13-20261026.md", "agent/task/carrybox-wall13-20261026.md", "docs/carrybox/wall13_20261026/README.md", "docs/carrybox/wall13_20261026/artifact_validation.json", "docs/carrybox/wall13_20261026/final_state.json", "docs/carrybox/wall13_20261026/receipts.json", "docs/carrybox/wall13_20261026/smoke.json", "docs/carrybox/wall13_20261026/smoke.log", "docs/carrybox/wall13_20261026/smoke.py", "docs/carrybox/wall13_20261026/smoke_model.pt", "docs/carrybox/wall13_20261026/validate.sh", "projects/README.md", "projects/findbox/README.md", "scripts/rsl_rl/play_carrybox_walled.sh", "scripts/rsl_rl/train_carrybox_walled.sh", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall13_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall13.py"]
task_contract_sha256: "9f2bb3f18707a809febb60f126d74137e1e6b38cf05cb00bddfbba18e2a35ae1"
tests: [{"command": "bash docs/carrybox/wall13_20261026/validate.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "bebb75c16d8dddfc278aebdd1d3b980f0ff3837f7afc1cb6982c720863f56989", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

新增wall13独立配置、环境身份、Gym注册及train/play shell入口，复用wall12全部行为与学习器。AMP显式选用canonical findbox revision3静止持箱数据（15段4155帧，hold300帧，第20帧后姿态固定且速度为0）。与wall12正式model19999的实际dataset元数据完全相同，因此本次没有数据内容变化；已告知用户并询问是否有另一路径，按已找到的匹配数据版本完成。

冻结检查PASS：环境配置仅variant不同，runner仅日志/运行名不同；片段哈希、静止尾段及AMP真实窗口通过；16环境24步/20次更新中actor、critic、CNN、pose head及AMP均更新且loss有限；checkpoint严格恢复、pose Adam状态通过，wall12严格恢复被拒绝。验证模型留docs，不是正式训练证据。未启动wall13正式训练、未评估收敛或4096性能，既有足球PID3814037仍运行。项目入口和看板已更新。
