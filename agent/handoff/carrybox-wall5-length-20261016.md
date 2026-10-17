---
task_id: "carrybox-wall5-length-20261016"
language: "zh-CN"
axes: ["E", "P", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["docs/carrybox/wall5_length_20261016/README.md", "docs/carrybox/wall5_length_20261016/analyze.py", "docs/carrybox/wall5_length_20261016/diagnosis_summary.json", "docs/carrybox/wall5_length_20261016/expert_brief.json", "docs/carrybox/wall5_length_20261016/expert_review.json", "docs/carrybox/wall5_length_20261016/receipts.json", "docs/carrybox/wall5_length_20261016/replay.log", "docs/carrybox/wall5_length_20261016/replay.py", "docs/carrybox/wall5_length_20261016/replay.sh", "docs/carrybox/wall5_length_20261016/replay_result.json", "docs/carrybox/wall5_length_20261016/source_hashes.json", "docs/carrybox/wall5_length_20261016/task_pre_metadata_correction.md", "docs/carrybox/wall5_length_20261016/training_curves.png", "docs/carrybox/wall5_length_20261016/training_rows.json", "docs/carrybox/wall5_length_20261016/training_summary.json", "docs/carrybox/wall5_length_20261016/artifact_validation.json", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-length-20261016.md", "agent/task/carrybox-wall5-length-20261016.md", "agent/report/carrybox-wall5-length-20261016.md", "agent/handoff/carrybox-wall5-length-20261016.md"]
task_contract_sha256: "ead77ad437a93bceb511704e5850b7272a413ea4f145ad505281d9493544e53c"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_length_20261016/analyze.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "42c44619a085a1cb8a034e39cd40f6531748909e26edbcaf55ad0493f2fc0ae1", "stdout_sha256": "7b038365b18e98ff887e94b37027851d8365d7928c074b9c95f93e9fa78ed10f", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_length_20261016/replay.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "517cd0ae188bb15bd13f9a508eef0facef4127d882e8fce7a5450331f57aa754", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

诊断已完成；不自动修改或重启训练。正式run为logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-16_13-45-09_wall5_amp_stage_a；21:57 JST的PID2996727与7396轮仅是带日期快照，后续操作必须重新只读核对。

证据入口docs/carrybox/wall5_length_20261016/README.md，原始四组记录replay_result.json，固定日志窗口training_summary.json，执行回执receipts.json。已完成有限值、严格schema2/revision9、零优化器更新、策略不变、终止计数/步数守恒及源码hash核验，无需重跑。

当前结论：推扰是短回合的重要因素，长存活仍未转为可靠接近和拾取；AMP阶段A有效但不等于G1完整任务迁移收敛。后续若授权修复，优先按能力开放push、核对朝箱移动/制动/拾取的奖励信号，再做辅助监督可见性与梯度审计。保留actor/critic深度+本体、AMP隔离、成功口径及真遮挡。无未完成必要诊断，无恢复命令。

单checkpoint、16环境、非严格配对和末尾未结束回合限制外推。不要用本次短测宣称正式成功率或历史回落的唯一因果。
