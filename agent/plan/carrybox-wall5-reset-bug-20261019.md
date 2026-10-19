---
task_id: "carrybox-wall5-reset-bug-20261019"
language: "zh-CN"
axes: ["E", "C", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "tests/test_carrybox_reset_bug.py", "docs/carrybox/wall5_reset_bug_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-reset-bug-20261019.md", "agent/task/carrybox-wall5-reset-bug-20261019.md", "agent/report/carrybox-wall5-reset-bug-20261019.md", "agent/handoff/carrybox-wall5-reset-bug-20261019.md"]
---

定位空手前倾、噪声膨胀和采样失衡；本次训练反馈修复包不涉及PD调参。旧训练已自行退出，不发送无对象信号。工程验收与后续策略收敛分开。
