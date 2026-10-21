---
task_id: "carrybox-wall5-rsi-pickup5-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "REPORT"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-rsi-pickup5-20261021.md", "agent/plan/carrybox-wall5-rsi-pickup5-20261021.md", "agent/report/carrybox-wall5-rsi-pickup5-20261021.md", "agent/task/carrybox-wall5-rsi-pickup5-20261021.md", "docs/carrybox/wall5_rsi_pickup5_20261021/README.md", "docs/carrybox/wall5_rsi_pickup5_20261021/artifact_validation.json", "docs/carrybox/wall5_rsi_pickup5_20261021/before.json", "docs/carrybox/wall5_rsi_pickup5_20261021/carrybox_wall5.py.before", "docs/carrybox/wall5_rsi_pickup5_20261021/carrybox_wall5_env_cfg.py.before", "docs/carrybox/wall5_rsi_pickup5_20261021/check.json", "docs/carrybox/wall5_rsi_pickup5_20261021/check.log", "docs/carrybox/wall5_rsi_pickup5_20261021/check.py", "docs/carrybox/wall5_rsi_pickup5_20261021/check.sh", "docs/carrybox/wall5_rsi_pickup5_20261021/formal_status.json", "docs/carrybox/wall5_rsi_pickup5_20261021/receipts.json", "projects/README.md", "projects/findbox/README.md", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py"]
task_contract_sha256: "1e77119641ae4cc8581d15fd8a85cd6bd8862a19c8f9d1d3688aedeba95797b8"
tests: [{"command": "bash docs/carrybox/wall5_rsi_pickup5_20261021/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "e0454dca2bbb18e0d89976cd04f168089f8a7973766152532cde94594575bbeb", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
---

wall5默认RSI由loco80% / pickup0% / hold20%改为75% / 5% / 20%；从loco让出5个百分点给地面pickup。

20环境reset检查通过，4096配额3072/205/819；既有0–31帧限制及AMP40/40/20保持。完整checkpoint契约只有两项RSI比例不同，旧模型直接resume拒绝；生产其他文件hash不变。

后台PID570043于2026-10-21T12:42:49.157757+09:00核对仍为原训练命令=True。本次未停止或重启，它仍使用启动时的80/0/20。新默认75/5/20在下一次创建环境/启动训练时生效。

详情：docs/carrybox/wall5_rsi_pickup5_20261021/README.md。检查已完成，无待恢复动作。
