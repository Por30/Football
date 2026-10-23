---
task_id: "carrybox-wall5-rev22-comparison-20261022"
language: "zh-CN"
axes: ["L"]
risk_tier: "T0"
status: "NO_CODE_CHANGE"
changed_files: ["agent/handoff/carrybox-wall5-rev22-comparison-20261022.md", "agent/plan/carrybox-wall5-rev22-comparison-20261022.md", "agent/report/carrybox-wall5-rev22-comparison-20261022.md", "agent/task/carrybox-wall5-rev22-comparison-20261022.md", "docs/carrybox/wall5_rev22_comparison_20261022/README.md", "docs/carrybox/wall5_rev22_comparison_20261022/artifact_validation.json", "docs/carrybox/wall5_rev22_comparison_20261022/check.py", "docs/carrybox/wall5_rev22_comparison_20261022/comparison.json", "docs/carrybox/wall5_rev22_comparison_20261022/receipts.json", "docs/carrybox/wall5_status_20261022_2338/README.md", "docs/carrybox/wall5_training_audit_20261022/README.md", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "5b3d4bd4e6b6b0d0088901a4ec0feea092416c8804ed1ec9f7d81f049258fefa"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_rev22_comparison_20261022/check.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "0a9abadb6302bc085cd7f63b27a0bed675d250e0291627d722d6217019932019", "stdout_sha256": "955737d6ab1567d441391e3aff3677d94b0aa2551b09cff50fb943f7dfa08374", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

核对用户指定rev22 model6400与当前rev26：力矩公式/权重、PD/控制周期相同；同到1200轮空手约49.5 vs 6.9步。撤回仅依据PhysHSI差异优先改力矩的判断；rev22行走阶段AMP style也约0.024，不能单凭低分归因。排查应回到rev23奖励/碰撞/专家数据变化，再看后续reset/延迟；未改训练。

本记录更正此前优先改力矩的建议。下一步以已能行走的rev22为基线隔离实际变化；没有未完成执行，也不自动修改或重启。
