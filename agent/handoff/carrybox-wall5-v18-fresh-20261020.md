---
task_id: "carrybox-wall5-v18-fresh-20261020"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-v18-fresh-20261020.md", "agent/plan/carrybox-wall5-v18-fresh-20261020.md", "agent/report/carrybox-wall5-v18-fresh-20261020.md", "agent/task/carrybox-wall5-v18-fresh-20261020.md", "docs/carrybox/wall5_v18_fresh_20261020/README.md", "docs/carrybox/wall5_v18_fresh_20261020/finish.py", "docs/carrybox/wall5_v18_fresh_20261020/launch.json", "docs/carrybox/wall5_v18_fresh_20261020/launch.py", "docs/carrybox/wall5_v18_fresh_20261020/launch.sh", "docs/carrybox/wall5_v18_fresh_20261020/receipts.json", "docs/carrybox/wall5_v18_fresh_20261020/snapshot.json", "docs/carrybox/wall5_v18_fresh_20261020/source_snapshot/scripts/rsl_rl/cli_args.py", "docs/carrybox/wall5_v18_fresh_20261020/source_snapshot/scripts/rsl_rl/train.py", "docs/carrybox/wall5_v18_fresh_20261020/source_snapshot/source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "docs/carrybox/wall5_v18_fresh_20261020/source_snapshot/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "docs/carrybox/wall5_v18_fresh_20261020/source_snapshot/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "docs/carrybox/wall5_v18_fresh_20261020/source_snapshot/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "docs/carrybox/wall5_v18_fresh_20261020/source_snapshot/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "docs/carrybox/wall5_v18_fresh_20261020/source_snapshot/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "docs/carrybox/wall5_v18_fresh_20261020/source_snapshot/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "docs/carrybox/wall5_v18_fresh_20261020/stopped_run.json", "docs/carrybox/wall5_v18_fresh_20261020/verify.log", "docs/carrybox/wall5_v18_fresh_20261020/verify.py", "docs/carrybox/wall5_v18_fresh_20261020/verify.sh", "logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-20_12-48-36_wall5_v18_distance3d_fresh_20261020_124832/model_0.pt", "logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-20_12-48-36_wall5_v18_distance3d_fresh_20261020_124832/params/agent.yaml", "logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-20_12-48-36_wall5_v18_distance3d_fresh_20261020_124832/params/env.yaml", "logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v18_distance3d_fresh_20261020_124832.log", "projects/README.md", "projects/findbox/README.md"]
task_contract_sha256: "3147884646d6ca9e907052dd005d1548352deeb690c8599a70cd0b7a1ce281f7"
tests: [{"command": "bash docs/carrybox/wall5_v18_fresh_20261020/verify.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "d71d809e138cc1f0ddc0b95913c29806485fd634668b1b7df7c97ca7653ecb4c", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
artifact: "HANDOFF"
---

旧revision17 PID254358已退出，历史日志和model_14800.pt保留。新版revision18三维距离训练已从零启动，4096环境、seed42、40000轮，PID553495；检查至16轮，最近10轮平均3.718秒、最慢3.750秒。首模型确认XYZ距离0.7m、schema2/revision18、非对称AC及13段60维AMP，优化器/Normalizer为全新初始化。正式训练进行中，尚未证明抱箱成功。

新日志：/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v18_distance3d_fresh_20261020_124832.log

新run：/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-20_12-48-36_wall5_v18_distance3d_fresh_20261020_124832

不要重复执行launch.sh；下一次任务先核对launch.json的真实PID和完整命令。新run没有加载任何旧checkpoint。生产源码沿用上一任务revision18并已有快照，既有暂存修改和历史工件保留。长期稳定性和拾箱能力需要后续独立回放，不能用启动PASS代替。
