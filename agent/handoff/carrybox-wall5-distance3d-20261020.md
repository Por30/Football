---
task_id: "carrybox-wall5-distance3d-20261020"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-distance3d-20261020.md", "agent/plan/carrybox-wall5-distance3d-20261020.md", "agent/report/carrybox-wall5-distance3d-20261020.md", "agent/task/carrybox-wall5-distance3d-20261020.md", "docs/carrybox/wall5_distance3d_20261020/README.md", "docs/carrybox/wall5_distance3d_20261020/attempt1_receipts.json", "docs/carrybox/wall5_distance3d_20261020/attempt1_smoke.log", "docs/carrybox/wall5_distance3d_20261020/attempt2_receipts.json", "docs/carrybox/wall5_distance3d_20261020/attempt2_smoke.log", "docs/carrybox/wall5_distance3d_20261020/check.log", "docs/carrybox/wall5_distance3d_20261020/check.sh", "docs/carrybox/wall5_distance3d_20261020/formal_status.json", "docs/carrybox/wall5_distance3d_20261020/prior_trajectory_geometry.json", "docs/carrybox/wall5_distance3d_20261020/receipts.json", "docs/carrybox/wall5_distance3d_20261020/repair_notes.json", "docs/carrybox/wall5_distance3d_20261020/rev17_contract_model.pt", "docs/carrybox/wall5_distance3d_20261020/smoke.json", "docs/carrybox/wall5_distance3d_20261020/smoke.log", "docs/carrybox/wall5_distance3d_20261020/smoke.py", "docs/carrybox/wall5_distance3d_20261020/smoke.sh", "docs/carrybox/wall5_distance3d_20261020/smoke_model.pt", "docs/carrybox/wall5_distance3d_20261020/source_hashes.json", "projects/README.md", "projects/findbox/README.md", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "tests/test_carrybox_distance3d.py"]
task_contract_sha256: "77a44db736a37543544d46256408724b94c7537551b03808728fc90a135aa945"
tests: [{"command": "bash docs/carrybox/wall5_distance3d_20261020/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "9bbf05dfd66b13ae759984795e1fd16243270093d11f2a73059a8308bfa40338", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_distance3d_20261020/smoke.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "8644c02d42a16a273a08a5e3b32f6675d0ccf46634fbe0431f315dec76cb377c", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

wall5 revision18将任务门控统一为骨盆到箱心XYZ距离0.7m，行走方向/AMP封顶仍为XY；43项CPU及4环境PPO/AMP 2＋1轮、严格恢复/旧契约拒绝通过。仅实现与短测，未重启；检查时正式PID254358仍为revision17、迭代14676，新版尚未正式训练或证明抱箱成功。

代码分布：wall5配置启用task_box_distance_3d；共享walled helper默认保留XY，供搜索和x2_rewards使用；wall5 walk/stability/日志统一调用helper。所有观察、数据、训练超参和旧wall任务接口保持。schema仍2，环境revision18；旧17严格load拒绝。详细验收/初次短测fixture修正见docs/carrybox/wall5_distance3d_20261020/README.md、receipts.json、smoke.json。

本次用户只要求修改距离，没有正式重启。下次操作进程前应重新核对formal_status.json对应PID及命令，勿以旧快照认定仍在运行。旧rev17播放应使用既有归档源；旧训练优化器不可按rev18严格恢复。若用户要求重启，按当次要求选择fresh或显式warm-start。短测模型不作为正式训练/成功率证据。
