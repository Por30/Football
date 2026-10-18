---
task_id: "carrybox-wall5-pickup-reset-20261017"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "NO_CODE_CHANGE"
changed_files: ["docs/carrybox/wall5_pickup_reset_20261017/README.md", "docs/carrybox/wall5_pickup_reset_20261017/audit.py", "docs/carrybox/wall5_pickup_reset_20261017/receipts.json", "docs/carrybox/wall5_pickup_reset_20261017/snapshot.json", "docs/carrybox/wall5_pickup_reset_20261017/artifact_validation.json", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-pickup-reset-20261017.md", "agent/task/carrybox-wall5-pickup-reset-20261017.md", "agent/report/carrybox-wall5-pickup-reset-20261017.md", "agent/handoff/carrybox-wall5-pickup-reset-20261017.md"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_pickup_reset_20261017/audit.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "7497dcbee3b1974e19649a5080a4118772239357db933d78b6388055f9f17970", "stdout_sha256": "88694ec321fabd77a70f256a5af15c158a36f2709d0961155e4671047fc738e8", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
task_contract_sha256: "af5fc15a7ca85b88b78dad5547509124f26b0467f2a0097fd8a20cb1d7c36980"
artifact: "HANDOFF"
resume_command: null
---

稳定状态：无CarryBox进程，football v5运行；旧正式run停在20786/40000，未完成长训，当前全身碰撞revision10仅短测。新诊断工件与项目入口已更新；没有GPU回放、参数调整或重启。后续建议先核对地面起点的G1手箱接触，再改奖励和推扰课程；候选原因尚无因果消融。保留全部既有全身碰撞改动。
