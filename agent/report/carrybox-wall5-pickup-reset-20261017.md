---
task_id: "carrybox-wall5-pickup-reset-20261017"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "NO_CODE_CHANGE"
changed_files: ["docs/carrybox/wall5_pickup_reset_20261017/README.md", "docs/carrybox/wall5_pickup_reset_20261017/audit.py", "docs/carrybox/wall5_pickup_reset_20261017/receipts.json", "docs/carrybox/wall5_pickup_reset_20261017/snapshot.json", "docs/carrybox/wall5_pickup_reset_20261017/artifact_validation.json", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-pickup-reset-20261017.md", "agent/task/carrybox-wall5-pickup-reset-20261017.md", "agent/report/carrybox-wall5-pickup-reset-20261017.md", "agent/handoff/carrybox-wall5-pickup-reset-20261017.md"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_pickup_reset_20261017/audit.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "7497dcbee3b1974e19649a5080a4118772239357db933d78b6388055f9f17970", "stdout_sha256": "88694ec321fabd77a70f256a5af15c158a36f2709d0961155e4671047fc738e8", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
task_contract_sha256: "af5fc15a7ca85b88b78dad5547509124f26b0467f2a0097fd8a20cb1d7c36980"
artifact: "REPORT"
---

完成只读诊断，未修改生产代码、模型、数据或进程。末100轮约556步、AMP占净混合奖励91.7%、loco累计成功0；CPU核验model20600 revision9及参考台高，记录奖励局部行为、RSI/地面差异和推扰候选。准确列出姿态/高度/超时reset、非有限值抛异常、成功不reset。当前revision10未正式训练；旧7200回放仅作已有证据，不称20600新评估。详见docs/carrybox/wall5_pickup_reset_20261017/README.md，单条CPU审计PASS。
