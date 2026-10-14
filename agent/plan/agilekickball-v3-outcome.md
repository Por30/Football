---
task_id: "AGILE-V3-OUTCOME-20261003"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/contact_outcome.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "tests/test_contact_outcome.py", "tests/test_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "scripts/rsl_rl/train_agilekickball_v3.sh", "docs/agilekickball_v3/README.md", "docs/agilekickball_v3/outcome_20261003", "README.md", "agent/plan/agilekickball-v3-outcome.md", "agent/task/agilekickball-v3-outcome.md", "agent/report/agilekickball-v3-outcome.md", "agent/handoff/agilekickball-v3-outcome.md"]
---

在现有 v3 空间扩展上实现 v2 兼容的训练期短时后果辅助。共享视觉编码器，当前动作条件预测 8 控制步后球速、身体倾斜/高度和窗口 kick proxy。验收：有效标签、反向传播、推理无特权泄漏、KL 回退、恢复一致，真实仿真两次更新。保留旧验证输出；不宣称性能已提升。
