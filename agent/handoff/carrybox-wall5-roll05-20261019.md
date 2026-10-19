---
task_id: "carrybox-wall5-roll05-20261019"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "tests/test_carrybox_training_v12.py", "docs/carrybox/wall5_roll05_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-roll05-20261019.md", "agent/task/carrybox-wall5-roll05-20261019.md", "agent/report/carrybox-wall5-roll05-20261019.md", "agent/handoff/carrybox-wall5-roll05-20261019.md"]
task_contract_sha256: "5f28d8617bfb2bf992ea0d91960caedabf7f2b21d82050a8de596d4a4087680f"
tests: [{"command": "bash docs/carrybox/wall5_roll05_20261019/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "551d9f6a1057ff084227d3056d4751c8eee964413ac7898e64f3d44fd0bb423f", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

wall5 roll终止已由abs(roll)>0.8改为>0.5rad，checkpoint契约同步；pitch保持1.1rad，其余任务、观察/AMP/PD/奖励不改。14项既有CPU检查通过，未运行GPU仿真或启动训练。0.8/0.5分别约45.84/28.65度，新阈值更早终止侧倾并减少恢复空间，不构成稳定性改善或此前pitch失稳已修复的结论。生产仍为revision15基础参数变体，旧0.8契约不能直接严格resume；上次未通过的loco控制候选继续归档。详细路径及前后备份见docs/carrybox/wall5_roll05_20261019。
