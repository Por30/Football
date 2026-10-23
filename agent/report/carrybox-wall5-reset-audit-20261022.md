---
task_id: "carrybox-wall5-reset-audit-20261022"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-reset-audit-20261022.md", "agent/plan/carrybox-wall5-reset-audit-20261022.md", "agent/report/carrybox-wall5-reset-audit-20261022.md", "agent/task/carrybox-wall5-reset-audit-20261022.md", "docs/carrybox/wall5_reset_audit_20261022/README.md", "docs/carrybox/wall5_reset_audit_20261022/analyze.log", "docs/carrybox/wall5_reset_audit_20261022/analyze.py", "docs/carrybox/wall5_reset_audit_20261022/artifact_validation.json", "docs/carrybox/wall5_reset_audit_20261022/check.sh", "docs/carrybox/wall5_reset_audit_20261022/curve.json", "docs/carrybox/wall5_reset_audit_20261022/curve.json.attempt1", "docs/carrybox/wall5_reset_audit_20261022/evidence.png", "docs/carrybox/wall5_reset_audit_20261022/probe.json", "docs/carrybox/wall5_reset_audit_20261022/probe.log", "docs/carrybox/wall5_reset_audit_20261022/probe.log.attempt1", "docs/carrybox/wall5_reset_audit_20261022/probe.py", "docs/carrybox/wall5_reset_audit_20261022/probe.py.attempt1", "docs/carrybox/wall5_reset_audit_20261022/probe_partial.json", "docs/carrybox/wall5_reset_audit_20261022/process_status.json", "docs/carrybox/wall5_reset_audit_20261022/receipts.json", "docs/carrybox/wall5_reset_audit_20261022/receipts.json.attempt1", "docs/carrybox/wall5_reset_audit_20261022/repair1.json", "docs/carrybox/wall5_reset_audit_20261022/selection.json", "docs/carrybox/wall5_reset_audit_20261022/summarize.py", "docs/carrybox/wall5_reset_audit_20261022/summary.json", "docs/carrybox/wall5_reset_audit_20261022/training_analysis.json", "docs/carrybox/wall5_reset_audit_20261022/training_analysis.json.attempt1", "docs/carrybox/wall5_reset_audit_20261022/training_snapshot.log", "docs/carrybox/wall5_reset_audit_20261022/training_snapshot.log.attempt1", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "2a4f2ad28f37beb766bd4b038e9e1d5fae816bc20fc89dfd613381932bc39f26"
tests: [{"command": "bash docs/carrybox/wall5_reset_audit_20261022/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "40883d067948c174e200872a348db8da087696e05bc274b901d20e74691b0815", "stdout_sha256": "4e3ab8e0861be7844520dff3c4063bab425f51b073ce42e8fe3ca78354a9ee2e", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

revision24只读reset诊断：抽样20/53.33/13.33/13.33正确，但640初态的行走/拾箱/持箱脚底穿地>1mm分别86.6%/90.9%/100%；未立即触发终止。固定model800的64环境均值/采样/保持reset目标对照，空手策略约0.13–0.15秒全部侧倾，保持目标约0.9–1.0秒；日志1082轮近期空手约7步。确认接地缺陷并发现策略加速失稳，未认定单一根因。检查通过；未改生产或操作训练PID1760747。

证据与分母、采样限制见 docs/carrybox/wall5_reset_audit_20261022/README.md。640初态与每种64个首回合（三模式）均保存；实际roll触发与初态足底几何分开分析。保持reset目标不是平衡控制器；未做单独足底修正训练消融，因此不能证明穿地为唯一根因。

首次诊断因初态严格浮点相等退出，保留失败回执；修正为1e-5数值容差、最大实测差5.1e-7m，技能/帧精确一致。完整重跑通过，权重与生产源码hash、正式进程身份均保持。日志未以Episode_Termination占比冒充近期回合比例，低频舍入伪差未作为结论。
