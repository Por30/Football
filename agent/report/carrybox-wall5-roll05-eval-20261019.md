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
artifact: "REPORT"
---

本次开始时最新落盘的model5200没有学会稳定站立/行走。独立进程均值/采样动作各32个纯loco首回合，分别平均22.6875/21步（0.45375/0.42秒），范围0.32–0.64/0.26–0.62秒，全部tipped且均在第一次推扰前结束；fell/invalid/timeout/censored均0，无任何首回合存活1秒。终止姿态在reset前采集，未混入新回合；参数前后相同，实际训练更新0。

5165–5414轮日志差分估计loco平均19.71步、hold700.05步，已完成回合步数约10.1/89.9%。总mean_episode_length约158不能表示行走成功。位移约0.25m包含初始RSI速度和倾倒过程，不能作为已学会走路证据。

CPU身份/日志与两模式回放两条冻结检查均PASS；这表示诊断完整，不代表任务行为成功。严格环境契约与权重加载、独立进程初始物理和actor观察配对、首次步数/轨迹长度与终态、权重和源码hash检查均通过，专家只读复核无影响结论的问题。最大20秒窗口在所有首回合结束后提前停止，非遗漏删失样本。

生产源码、数据、checkpoint未改，正式训练PID114186持续运行，20:16:40日志5495轮；期间已产生model5400，该新模型未评估。本报告结论只属于锁定SHA的5200。证据和局限见docs/carrybox/wall5_roll05_eval_20261019/README.md、summary.json、training_audit.json及finish_snapshot.json。
