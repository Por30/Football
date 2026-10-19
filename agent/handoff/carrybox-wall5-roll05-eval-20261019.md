---
task_id: "carrybox-wall5-roll05-eval-20261019"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["docs/carrybox/wall5_roll05_eval_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-roll05-eval-20261019.md", "agent/task/carrybox-wall5-roll05-eval-20261019.md", "agent/report/carrybox-wall5-roll05-eval-20261019.md", "agent/handoff/carrybox-wall5-roll05-eval-20261019.md"]
task_contract_sha256: "8cc6e8f066a69e55370261bc796e9805620ae149f66c68bd7c566f54893921b7"
tests: [{"command": "bash docs/carrybox/wall5_roll05_eval_20261019/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "17b00c95b48acb913efb9be0fe4e6d47cb2ce9f56fa74baf9a7cc76c4b7a405e", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_roll05_eval_20261019/replay.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "91c7feb75c870606847ce376e87a0dd75f65e9d182a839e224f19fffe5f6cd1d", "stdout_sha256": "b9fe7d44fd5e50e2676e66975fc2cd729be01885e68846cf2edd1ddb223a0346", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

评估已完成，用户问题的答案是：检查时最新model5200尚未稳定站走，均值/采样各32个空手首回合全部在0.64秒内倾角超限reset。不能表述为全部已摔到地面（fell=0），也不能把0.25m位移当作受控步态。所有首次终止在push前，只排除这些首回合由推扰直接触发，不推断整个学习过程与推扰无关。

两个冻结命令回执PASS，完整首回合轨迹/终态、存活分母、timeout/censor、初态配对和权重不变有证据。source/数据/模型未改；正式训练从未暂停或停止。PID114186与日志路径见selection.json，结尾快照5495轮，latest_checkpoint_now为5400；不要把5200回放作为5400效果。再次评估时锁定当时最新完整模型及hash，不覆盖本目录历史结果。

工程报告DONE仅表示这次诊断完成，不表示稳定控制修复或正式40000轮结束。此前控制候选仍撤回，本任务没有启用或修正它。下一步若用户要求修复，需基于当前空手控制与样本分配证据开展明确任务，不沿用旧AMP主导假说或任意放宽终止。查证细节从docs/carrybox/wall5_roll05_eval_20261019/README.md开始。
