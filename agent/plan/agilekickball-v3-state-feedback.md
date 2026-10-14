---
task_id: "AGILE-V3-STATE-FEEDBACK-20261006"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/state_feedback.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/export.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_outcome_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3_outcome.py", "tests/test_state_feedback.py", "tests/test_agilekickball_v3.py", "tests/test_agilekickball_v3_outcome.py", "tests/test_contact_outcome.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "scripts/rsl_rl/train_agilekickball_v3.sh", "docs/agilekickball_v3/README.md", "docs/agilekickball_v3/state_feedback_20261006", "README.md", "logs", "agent/plan/agilekickball-v3-state-feedback.md", "agent/task/agilekickball-v3-state-feedback.md", "agent/report/agilekickball-v3-state-feedback.md", "agent/handoff/agilekickball-v3-state-feedback.md"]
---

重建与 v2 完全相同的物理任务，移除新任务中的旧未来后果辅助，加入本体融合球状态分布估计及置信度门控动作残差。保留主actor，从零训练，不移植预训练权重。完成有限回归和真实仿真后按用户授权后台启动4096环境50000轮。旧v3另保留Outcome任务用于读取历史checkpoint。
