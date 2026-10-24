---
task_id: "carrybox-wall10-physhsi-20261023"
language: "zh-CN"
axes: ["L", "D", "C", "P"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall10_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/play_carrybox_walled.sh", "tests/test_carrybox_wall10.py", "docs/carrybox/wall10_20261023", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall10-physhsi-20261023.md", "agent/task/carrybox-wall10-physhsi-20261023.md", "agent/report/carrybox-wall10-physhsi-20261023.md", "agent/handoff/carrybox-wall10-physhsi-20261023.md"]
artifact: "PLAN"
status: "DRAFT"
---

新增独立wall10，从本地PhysHSI G1搬箱任务迁移；保留原训练细节，actor以FindBox深度替代真值任务信息，critic保留训练专用真值。流程止于抬箱后原地保持，取消搬运目标和放下；短测工件只进入docs，不启动正式长训。
