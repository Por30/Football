---
task_id: "carrybox-wall5-training-audit-20261022"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-training-audit-20261022.md", "agent/plan/carrybox-wall5-training-audit-20261022.md", "agent/report/carrybox-wall5-training-audit-20261022.md", "agent/task/carrybox-wall5-training-audit-20261022.md", "docs/carrybox/wall5_training_audit_20261022/README.md", "docs/carrybox/wall5_training_audit_20261022/analyze.log", "docs/carrybox/wall5_training_audit_20261022/analyze.py", "docs/carrybox/wall5_training_audit_20261022/artifact_validation.json", "docs/carrybox/wall5_training_audit_20261022/check.sh", "docs/carrybox/wall5_training_audit_20261022/cpu.log", "docs/carrybox/wall5_training_audit_20261022/curve.json", "docs/carrybox/wall5_training_audit_20261022/finish.py", "docs/carrybox/wall5_training_audit_20261022/probe.json", "docs/carrybox/wall5_training_audit_20261022/probe.log", "docs/carrybox/wall5_training_audit_20261022/probe.py", "docs/carrybox/wall5_training_audit_20261022/probe_partial.json", "docs/carrybox/wall5_training_audit_20261022/process_status.json", "docs/carrybox/wall5_training_audit_20261022/receipts.json", "docs/carrybox/wall5_training_audit_20261022/selection.json", "docs/carrybox/wall5_training_audit_20261022/summarize.py", "docs/carrybox/wall5_training_audit_20261022/summary.json", "docs/carrybox/wall5_training_audit_20261022/training_analysis.json", "docs/carrybox/wall5_training_audit_20261022/training_snapshot.log", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "23ea21bc5570af5747b2a5c536a8d4ba16f7c8ba073069223bbfc489b543ca04"
tests: [{"command": "bash docs/carrybox/wall5_training_audit_20261022/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "dbd5d00bb9ba7d9c886fce7a2b7be5c07ae9505579157bfb38b6e333fb927768", "stdout_sha256": "d66e2a6dbfad2e93788878452eddf9a35aae92dc5c860c4f7a8ceb1323dcb693", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

revision26只读审查：日志截至401轮，空手近期约6步；model200的39个loco首回合，采样/均值动作约5步，保持reset目标约45步。确认当前原始力矩平方与PhysHSI除kp后平方同权重，在同批状态相差约1.9万倍；正式空手力矩及动作变化惩罚合计约为walk的1.95倍。AMP已饱和，但60维FK/坐标对齐，专家重复帧对照不支持将饱和单独归因于历史填充。14项CPU及64环境只读回放通过；未修改生产或停止/重启PID1796143，未认定单一失稳根因。

证据及每组分母见 docs/carrybox/wall5_training_audit_20261022/README.md。测试PASS表示诊断有效，不表示训练收敛。模型在开始时固定200轮、日志最终冻结401轮；没有将两者混为同一时刻。PPO终止bootstrap、reset前AMP、reward dt、特权隔离等未发现明显错误。辅助全帧系数1.0由用户指定，本段损失未爆炸，仅保留为远箱风险；未擅自改变。
