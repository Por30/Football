---
task_id: "carrybox-wall5-rsi-pickup5-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "docs/carrybox/wall5_rsi_pickup5_20261021", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-rsi-pickup5-20261021.md", "agent/task/carrybox-wall5-rsi-pickup5-20261021.md", "agent/report/carrybox-wall5-rsi-pickup5-20261021.md", "agent/handoff/carrybox-wall5-rsi-pickup5-20261021.md"]
artifact: "PLAN"
---

仅修改wall5 RSI默认分配为75/5/20，复用固定配额与既有贴地pickup采样。AMP、物理、观测、奖励和后台训练保持。验收实际配置/4096配额、20环境全部/部分/自动reset、旧新契约差异。
