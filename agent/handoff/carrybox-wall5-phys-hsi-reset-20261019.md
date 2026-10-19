---
task_id: "carrybox-wall5-phys-hsi-reset-20261019"
language: "zh-CN"
axes: ["L", "C"]
risk_tier: "T1"
status: "NO_CODE_CHANGE"
changed_files: ["docs/carrybox/wall5_physhsi_reset_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-phys-hsi-reset-20261019.md", "agent/task/carrybox-wall5-phys-hsi-reset-20261019.md", "agent/report/carrybox-wall5-phys-hsi-reset-20261019.md", "agent/handoff/carrybox-wall5-phys-hsi-reset-20261019.md"]
task_contract_sha256: "d8ccb9d1fcb28f4ffd229a090a9b9fbb7a0b33cc0b62fa7146d7e6bfa9c81710"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_physhsi_reset_20261019/check.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "a0859c30e10d980854e30b10458f34ba140c2323e4a961820340090016bbe586", "stdout_sha256": "d723fd3b8fc46803e437ea6ac3709f46ed9ff9be6f4ca95a05c7fc1c7833d4a6", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

完成本地PhysHSI与wall5 revision17 reset只读审计。源码及数据身份核验PASS，11段loco与PhysHSI原数据相同；当前参考起始水平速度均值0.743m/s、P95 1.071m/s，PhysHSI RSI覆盖速度的水平上限0.283m/s。PhysHSI实际20%默认站姿、53.33%loco RSI、13.33%pickup、13.33%hold，roll0.5/pitch1.1并不比wall5宽松。预填动作延迟缓存仅给0–20ms起始目标保持，不是动作平滑或冻结机器人。保持参考速度与缩小速度都有步态一致性权衡，尚未通过物理对照认定因果。未改生产源码、数据或训练配置；未启动/停止训练。22:12:47 JST快照PID254358运行至134轮，最近10轮3.80–3.87秒；不得将旧快照当实时状态。全部证据、详细调用链、影响解释与后续单项验证建议见docs/carrybox/wall5_physhsi_reset_20261019/README.md。
