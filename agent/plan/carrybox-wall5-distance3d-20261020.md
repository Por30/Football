---
task_id: "carrybox-wall5-distance3d-20261020"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "tests/test_carrybox_distance3d.py", "docs/carrybox/wall5_distance3d_20261020", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-distance3d-20261020.md", "agent/task/carrybox-wall5-distance3d-20261020.md", "agent/report/carrybox-wall5-distance3d-20261020.md", "agent/handoff/carrybox-wall5-distance3d-20261020.md"]
---

按用户提供的x2g1differ.md第3.9节和handoff.txt奖励公式，仅调整wall5任务距离语义。四处生产代码使用显式wall5开关，其他任务默认二维；不涉及网络、物理或数据调整。验收为边界数值、共享调用隔离、真实4环境PPO/AMP与契约恢复检查。
