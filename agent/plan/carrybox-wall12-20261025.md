---
task_id: "carrybox-wall12-20261025"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "READY"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall12.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall12.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall12_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall12.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/play_carrybox_walled.sh", "tests/test_carrybox_wall12.py", "docs/carrybox/wall12_20261025", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall12-20261025.md", "agent/task/carrybox-wall12-20261025.md", "agent/report/carrybox-wall12-20261025.md", "agent/handoff/carrybox-wall12-20261025.md"]
---

在wall11上增加深度CNN位姿监督。复用128→128→9 pose head与已有辅助loss hook，独立wall12 subclass；预测相机系位置/旋转，按可变箱尺寸处理对称，训练端标签与部署输入隔离。
