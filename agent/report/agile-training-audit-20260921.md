---
task_id: "ENG-AGILE-AUDIT-20260921"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "REPORT"
status: "DONE"
changed_files: ["scripts/rsl_rl/audit_agilekickball.py", "scripts/rsl_rl/audit_agilekickball.sh", "docs/agilekickball/training_audit_20260921/training_course_samples.pt", "docs/agilekickball/training_audit_20260921/receipts.json", "docs/agilekickball/training_audit_20260921/replay.log", "docs/agilekickball/training_audit_20260921/default_play_course_samples.pt", "docs/agilekickball/training_audit_20260921/README.md", "docs/agilekickball/training_audit_20260921/play_fix_receipts.json", "docs/agilekickball/training_audit_20260921/replay.json", "docs/agilekickball/training_audit_20260921/near_incoming.json", "docs/agilekickball/training_audit_20260921/tensorboard_summary.json", "agent/plan/agile-training-audit-20260921.md", "agent/task/agile-training-audit-20260921.md", "agent/report/agile-training-audit-20260921.md", "agent/handoff/agile-training-audit-20260921.md"]
task_contract_sha256: "faa2a3e958a4e30217d228a43fe6dc481a1a2a859d4e5733712742883168a44d"
tests: [{"command": "bash scripts/rsl_rl/audit_agilekickball.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "fd874a4d4a218bf5dda994ff634b17acf02e64cca0f2b9267a46d1367ac4d418", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
---

只读核查最新25369轮日志和model_25200。末100轮可见活动/来球/近脚速度向量RMSE为0.319/0.556/0.883m/s；近脚位置误差109.57cm，不准确。16环境20秒确定性对照：训练课程92次代理、94次恢复重发；旧默认播放9次代理、72次恢复重发，均0次reset。训练课程代理脚速2.231m/s，不能认定完全只学站立。发现play不恢复课程进度，另立局部修复合同ENG-AGILE-PLAY-COURSE-20260921完成修复。

详细指标、口径、原始证据及播放命令见docs/agilekickball/training_audit_20260921/README.md。速度标量与向量误差分开，不将代理次数写成成功率。关键近脚盲区尚未修复，CPU无梯度回放不代表真机或全部checkpoint。
