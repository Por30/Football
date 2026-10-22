---
task_id: "carrybox-wall5-grasp-20261022"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/carrybox_fullbody_collision.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/assets/motions/findbox/README.md", "source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup/README.md", "tests/test_carrybox_grasp.py", "docs/carrybox/wall5_grasp_20261022", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-grasp-20261022.md", "agent/task/carrybox-wall5-grasp-20261022.md", "agent/report/carrybox-wall5-grasp-20261022.md", "agent/handoff/carrybox-wall5-grasp-20261022.md"]
artifact: "PLAN"
status: "DRAFT"
---

wall5当前能接近并站稳，但三段地面回放手箱接触均为零。此次只优化拾箱相关奖励、恢复完整三段AMP并打开wall5自碰撞，使用现有短测/启动守护流程验证后正式从零4096训练。三段中高处起箱动作只进入AMP，RSI仍使用已验证地面片段。
