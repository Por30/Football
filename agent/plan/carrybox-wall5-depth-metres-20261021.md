---
task_id: "carrybox-wall5-depth-metres-20261021"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "tests/test_carrybox_depth_metres.py", "docs/carrybox/wall5_depth_metres_20261021", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-depth-metres-20261021.md", "agent/task/carrybox-wall5-depth-metres-20261021.md", "agent/report/carrybox-wall5-depth-metres-20261021.md", "agent/handoff/carrybox-wall5-depth-metres-20261021.md"]
---

wall5光轴深度由除以3的归一化值改为米；依据用户最新对照把Gaussian和立体噪声降至0.02/0.008–0.03m。保留critic108/rot6前两列、可见监督coef0.1，已异步询问用户其他对齐范围并给出此默认方案。保护延迟/冻结配对、未命中、遮挡、actor与部署一致性；修复后从零重启4096环境，不恢复旧输入尺度模型。