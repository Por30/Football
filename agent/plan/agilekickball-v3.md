---
task_id: "AGILE-V3-20260927"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_state.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "tests/test_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "docs/agilekickball_v3", "README.md", "agent/plan/agilekickball-v3.md", "agent/task/agilekickball-v3.md", "agent/report/agilekickball-v3.md", "agent/handoff/agilekickball-v3.md"]
---

在v2基础上新增独立v3，只调空间参数组。T2单学习轴SYSTEM_TUNING，由当前Agent直接完成。距离由0.5–0.7m渐进到1.3–3m，横向目标偏移由±0.25m渐进到±0.75m（均用60000平均来球曝光步），移动终止半径0.6→1.2m。速度、奖励、恢复和网络继承v2。
