---
task_id: "carrybox-wall5-length-20261016"
language: "zh-CN"
axes: ["E", "P", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["docs/carrybox/wall5_length_20261016/README.md", "docs/carrybox/wall5_length_20261016/analyze.py", "docs/carrybox/wall5_length_20261016/diagnosis_summary.json", "docs/carrybox/wall5_length_20261016/expert_brief.json", "docs/carrybox/wall5_length_20261016/expert_review.json", "docs/carrybox/wall5_length_20261016/receipts.json", "docs/carrybox/wall5_length_20261016/replay.log", "docs/carrybox/wall5_length_20261016/replay.py", "docs/carrybox/wall5_length_20261016/replay.sh", "docs/carrybox/wall5_length_20261016/replay_result.json", "docs/carrybox/wall5_length_20261016/source_hashes.json", "docs/carrybox/wall5_length_20261016/task_pre_metadata_correction.md", "docs/carrybox/wall5_length_20261016/training_curves.png", "docs/carrybox/wall5_length_20261016/training_rows.json", "docs/carrybox/wall5_length_20261016/training_summary.json", "docs/carrybox/wall5_length_20261016/artifact_validation.json", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-length-20261016.md", "agent/task/carrybox-wall5-length-20261016.md", "agent/report/carrybox-wall5-length-20261016.md", "agent/handoff/carrybox-wall5-length-20261016.md"]
task_contract_sha256: "ead77ad437a93bceb511704e5850b7272a413ea4f145ad505281d9493544e53c"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_length_20261016/analyze.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "42c44619a085a1cb8a034e39cd40f6531748909e26edbcaf55ad0493f2fc0ae1", "stdout_sha256": "7b038365b18e98ff887e94b37027851d8365d7928c074b9c95f93e9fa78ed10f", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_length_20261016/replay.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "517cd0ae188bb15bd13f9a508eef0facef4127d882e8fce7a5450331f57aa754", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

完成当前wall5平均回合长度诊断。仅新增诊断脚本、证据与项目文档；没有修改生产代码/模型/数据或停止、重启训练。诊断完成不等于修复完成或正式训练收敛。

固定model_7200、16环境四组纯推理，采样动作有/无push完成均值277.09/531.11步，均值动作有/无push239.97/545.63步；同等19200环境步内跌倒或倾倒56→15、61→16，支持当前策略推扰恢复不足。四组loco成功0；无push组距箱约6.3–6.5m、近箱约13%，延长存活未解决目标接近和拾取。每组16个未结束回合单列，成功也包含未结束hold记录；RSI成功不当作完整任务成功。

实际PPO lr=3e-4、AMP净混合奖励占比约75.2%，判别器未再次饱和；旧普遍3步reset未复现。动作采样不是整体短回合的充分解释。任务奖励局部行为和辅助监督梯度干扰是后续候选，未做重训消融，不宣称唯一根因。

两条冻结命令PASS，策略逐张量未变，生产源码hash未变，所有状态有限，步数守恒；原只读专家复核一致。工件字段映射更正保留原合同和hash，详见expert_review.json，不改变已执行测试或范围。

21:57 JST复核正式PID2996727仍运行，7396轮、最近100轮日志均值290.00步；并发诊断退出后训练约4.09秒/轮。详细数字、方法和边界见docs/carrybox/wall5_length_20261016/README.md。
