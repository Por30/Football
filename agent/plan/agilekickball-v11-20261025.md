---
task_id: "agilekickball-v11-20261025"
language: "zh-CN"
axes: ["L", "P", "D", "C"]
risk_tier: "T2"
artifact: "PLAN"
status: "READY"
allowed_paths: ["source/perceptual_ball/perceptual_ball/kickball_v11.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/kickball_v11.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/kickball_v11_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_v11.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/train_kickball_v11.sh", "scripts/rsl_rl/play_kickball_v11.sh", "tests/test_kickball_v11.py", "docs/kickball_v11", "projects/README.md", "projects/football/README.md", "agent/plan/agilekickball-v11-20261025.md", "agent/task/agilekickball-v11-20261025.md", "agent/report/agilekickball-v11-20261025.md", "agent/handoff/agilekickball-v11-20261025.md"]
---

基于wall11框架构建独立足球任务；以v4连续回传为任务语义。默认从零训练，完成工程及短测，不启动正式长训。
