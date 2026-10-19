---
task_id: "carrybox-wall5-roll05-start-20261019"
language: "zh-CN"
axes: ["A"]
risk_tier: "T1"
status: "DONE"
changed_files: ["docs/carrybox/wall5_roll05_start_20261019", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-roll05-start-20261019.md", "agent/task/carrybox-wall5-roll05-start-20261019.md", "agent/report/carrybox-wall5-roll05-start-20261019.md", "agent/handoff/carrybox-wall5-roll05-start-20261019.md"]
task_contract_sha256: "073b7c8462f344e51f59c5fd3f6b206a8b91a9c26ffa8b38ec52d12ae8afdcda"
tests: [{"command": "bash docs/carrybox/wall5_roll05_start_20261019/verify.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "e44506b1d6455bd9048c6f3cc4b29bdbd108c27e391b4af6d6782bf1089acb7f", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "REPORT"
---

wall5已按用户新指令从零正式启动，PID114186，4096环境、seed42、40000轮，无resume/warm-start。检查时间2026-10-19T14:31:55.348542+09:00，迭代1→16；最近10轮平均3.802秒、最慢3.900秒。首checkpoint确认revision15＋roll0.5、RSI80/0/20、13段60维AMP、独立108维critic；actor仍深度＋本体，增量push与1.0/multiply摩擦已生效。优化器及AMP统计是全新初始化，参数有限。生产代码未修改，先前未通过的loco控制候选未启用。训练进行中，尚未证明站走或拾箱收敛。

Run：/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_14-25-38_wall5_v15_roll05_fresh_20261019_142533。日志：/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v15_roll05_fresh_20261019_142533.log。

本任务完成的是用户明确要求的正式启动及运行核验，不是修复控制问题或完成40000轮训练。进程留在后台，后续先核对launch.json及真实PID命令；不得重复启动或用文档快照推断实时状态。详细证据、分技能初期指标和复现命令见docs/carrybox/wall5_roll05_start_20261019/README.md。
