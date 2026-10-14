---
task_id: "carrybox-findbox-amp"
language: "zh-CN"
axes: ["E", "L", "S"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_amp.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox.py", "tests/test_carrybox_amp.py", "scripts/rsl_rl/smoke_carrybox.py", "docs/carrybox", "findbox/amp_manifest.json", "README.md", "agent"]
---

将用户指定findbox的17段动作接入现有CarryBox AMP，复用现有LSGAN判别器，保留深度与位姿监督路径。验收真实动作加载、有限梯度、reset/terminal无跨界、checkpoint和无数据集推理。
