---
task_id: "carrybox-wall5-headfix-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "PLAN"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_reward_geometry.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "tests/test_carrybox_reward_geometry.py", "docs/carrybox/wall5_headfix_20261021", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-headfix-20261021.md", "agent/task/carrybox-wall5-headfix-20261021.md", "agent/report/carrybox-wall5-headfix-20261021.md", "agent/handoff/carrybox-wall5-headfix-20261021.md"]
---

核对用户更正，将 wall5 头高标定改为 X2 1.112 m，移除 early_failure，将低骨盆和低头终止分开记录。保持骨盆/箱子标定、3D距离、RSI75/5/20、roll0.5及其他训练配置。验证后停止身份匹配的旧进程，新建4096环境正式run从头训练，保留全部旧模型与日志。X2数字如无本地资产只能注明用户提供，不能冒称独立FK验证。
