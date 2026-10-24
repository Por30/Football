---
task_id: "carrybox-physhsi-full-audit-20261023"
language: "zh-CN"
axes: ["L", "C", "E", "P"]
risk_tier: "T2"
status: "NO_CODE_CHANGE"
changed_files: ["agent/handoff/carrybox-physhsi-full-audit-20261023.md", "agent/plan/carrybox-physhsi-full-audit-20261023.md", "agent/report/carrybox-physhsi-full-audit-20261023.md", "agent/task/carrybox-physhsi-full-audit-20261023.md", "docs/carrybox/physhsi_full_audit_20261023/README.md", "docs/carrybox/physhsi_full_audit_20261023/appendix.md", "docs/carrybox/physhsi_full_audit_20261023/artifact_validation.json", "docs/carrybox/physhsi_full_audit_20261023/build_appendix.py", "docs/carrybox/physhsi_full_audit_20261023/check_data.py", "docs/carrybox/physhsi_full_audit_20261023/check_sources.py", "docs/carrybox/physhsi_full_audit_20261023/data.json", "docs/carrybox/physhsi_full_audit_20261023/document_checks.json", "docs/carrybox/physhsi_full_audit_20261023/effective_parameters.tsv", "docs/carrybox/physhsi_full_audit_20261023/expert_brief.json", "docs/carrybox/physhsi_full_audit_20261023/finish.py", "docs/carrybox/physhsi_full_audit_20261023/inspect_usd.py", "docs/carrybox/physhsi_full_audit_20261023/receipts.json", "docs/carrybox/physhsi_full_audit_20261023/reconstruction.md", "docs/carrybox/physhsi_full_audit_20261023/source_identity.json", "docs/carrybox/physhsi_full_audit_20261023/sources.json", "docs/carrybox/physhsi_full_audit_20261023/wall10_supplement.json", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "f4c79bca2ab5851b047b03f285416394fe7521119ee4809e83a7e45c72a22c34"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/physhsi_full_audit_20261023/check_sources.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "4751c50eb999e5c26a351f128739bb1fadddea725ae368c2c8bf5f49cc1cd285", "stdout_sha256": "1c7772b08bee2573aa854e055b93e47f9e93ba44ac0045dd827ce584b8389b98", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/physhsi_full_audit_20261023/check_data.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "2414bef680c515f8c84d53653119c2cff8c0dcf958eae4acdf95e06e2d4fe167", "stdout_sha256": "1243d01d346f9541f6874cee7c0f3bb441c5ef5edb8daffb66fb6ba3bd171ae9", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

完成wall5 rev28对本地PhysHSI G1 carrybox/resume全链路只读审计：47个文件身份、1719个展开参数叶项、19/15段数据及14段字节同源、URDF/USD质量、网络CPU前向与全部有效奖励/AMP/PPO/reset/控制比较。源actor使用箱子/goal状态而当前使用深度；显式/隐式PD、力矩定义、100/24步rollout、时序平滑、数据采样与任务成功语义存在实质差异。同步独立wall10现状与性能证据，不将差异当作已证实失稳根因。未修改生产或操作训练；重构尚未实施。

无待恢复命令或本任务GPU进程。后续重构以reconstruction.md为依据，不能自动把此审计解释为启动训练。本轮主对照是wall5 rev28 model5600与正式params；wall10是已有独立任务，不能混用checkpoint。两条CPU命令和源文件hash分别见receipts.json/source_identity.json。注意源actor真值、显式PD、源reward尺度、100步与24步预算、static hold数据改造，以及源history/feet缓存顺序问题。
