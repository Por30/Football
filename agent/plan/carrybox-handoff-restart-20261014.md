---
task_id: "carrybox-handoff-restart-20261014"
language: "zh-CN"
axes: ["L", "P", "C"]
risk_tier: "T2"
artifact: "PLAN"
status: "READY"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "source/perceptual_ball/perceptual_ball/carrybox_walled.py", "tests/test_carrybox_walled.py", "tests/test_carrybox_x2.py", "scripts/rsl_rl/validate_carrybox_handoff.py", "scripts/rsl_rl/validate_carrybox_handoff.sh", "scripts/rsl_rl/benchmark_carrybox_warp.py", "handoff.txt", "docs/carrybox/handoff_20261014", "README.md", "projects/README.md", "projects/findbox/README.md", "logs/rsl_rl/g1_carrybox_depth", "agent/plan/carrybox-handoff-restart-20261014.md", "agent/task/carrybox-handoff-restart-20261014.md", "agent/report/carrybox-handoff-restart-20261014.md", "agent/handoff/carrybox-handoff-restart-20261014.md"]
---

按handoff.txt更新G1 wall3/wall4的RSI比例、完整奖励、双向roll终止及传感器/物理随机化。保留G1四帧深度/本体、无特权critic、纯本体AMP及新版15段数据。新环境契约revision6。验证后4096环境新run从最近正式权重warm-start；不恢复旧PPO/AMP。
