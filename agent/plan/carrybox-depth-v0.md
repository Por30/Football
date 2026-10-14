---
task_id: "carrybox-depth-v0"
language: "zh-CN"
axes: ["E", "P", "L", "D"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/assets/motions/carrybox", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/smoke_carrybox.py", "scripts/rsl_rl/smoke_carrybox.sh", "tests/test_carrybox.py", "docs/carrybox", "README.md", "agent"]
---

参考 PhysHSI 接近与拾起奖励，独立移植为真实深度输入的拾箱任务。验收覆盖无真值泄漏、监督梯度、接触保持成功、物理reset与PPO/checkpoint。已有未提交修改保留。
