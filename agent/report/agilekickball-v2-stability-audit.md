---
task_id: "AGILE-V2-STABILITY-AUDIT-20260924"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/agilekickball-v2-stability-audit.md", "agent/plan/agilekickball-v2-stability-audit.md", "agent/report/agilekickball-v2-stability-audit.md", "agent/task/agilekickball-v2-stability-audit.md", "docs/agilekickball_v2/stability_audit_20260924/REPORT.md", "docs/agilekickball_v2/stability_audit_20260924/artifacts.json", "docs/agilekickball_v2/stability_audit_20260924/metrics.json", "docs/agilekickball_v2/stability_audit_20260924/receipts.json", "docs/agilekickball_v2/stability_audit_20260924/replay.json", "docs/agilekickball_v2/stability_audit_20260924/replay.py", "docs/agilekickball_v2/stability_audit_20260924/run_replay.sh"]
task_contract_sha256: "51110795e8477c4cfdfe9a7759413f8d01f8c53a9437e338ff572655231cd677"
tests: [{"command": "bash docs/agilekickball_v2/stability_audit_20260924/run_replay.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "4ad9cc29182adcc4e7a1a1b238320ac1fd9fc4f3d860bf6a2ab2a67d038dfba4", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

# v2稳定性只读审计

已完成训练配置核对、相同轮数日志比较及CPU16环境3策略×3条件×800步回放；冻结命令通过。所有终止类型按真实done采样，计数总和验证等于总终止数。

当前v2在约1.05万轮时，最近1000轮平均episode1.16s，恢复后发球比例0；同轮数v1为9.68s、38.06%。v2会主动踢球，但随后跑离锚点，严格闭环成功为0。直接将当前v2权重换成v1恢复规则仍226次离锚点终止、0次恢复发球；成熟v1权重在v2恢复规则正常连续运行。早期v1策略对缩短距离显著受益。

最强怀疑是前期距离课程推进过快与即时踢球奖励/失败处理不匹配；窗口几乎饱和到0.4s是额外设计问题。不能把短推理回放当成各训练机制的独立因果消融。完整口径、数据和下一步建议见docs/agilekickball_v2/stability_audit_20260924/REPORT.md。

生产代码和运行中的GPU训练均未修改；当前训练未被暂停。用户后续若要求修复，应单独冻结训练修改范围，先恢复可靠近距离起步、明确闭环奖励和失败处理，再验证课程加速；不要直接改磁盘文件后声称正在运行的训练已生效。
