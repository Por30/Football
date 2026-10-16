---
task_id: "carrybox-wall5-20261016"
language: "zh-CN"
axes: ["L", "E"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/train_carrybox_walled.sh", "tests/test_carrybox_wall5.py", "docs/carrybox/wall5_20261016", "README.md", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-20261016.md", "agent/task/carrybox-wall5-20261016.md", "agent/report/carrybox-wall5-20261016.md", "agent/handoff/carrybox-wall5-20261016.md"]
artifact: "PLAN"
status: "READY"
---

依照x2g1differ.md第6节阶段A实施P0组：AMP幅度、特征、正则化与首步窗口。保持PPO、4帧深度、共享critic、RSI、物理任务与15段原始数据不变，便于对照；P1/P2明确留待后续，不启动正式训练。
