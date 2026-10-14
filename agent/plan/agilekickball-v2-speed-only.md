---
task_id: "AGILE-V2-SPEED-ONLY-20260925"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v2.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v2_env_cfg.py", "tests/test_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.sh", "docs/agilekickball_v2", "README.md", "agent/plan/agilekickball-v2-speed-only.md", "agent/task/agilekickball-v2-speed-only.md", "agent/report/agilekickball-v2-speed-only.md", "agent/handoff/agilekickball-v2-speed-only.md"]
---

恢复v1已验证的连续球行为；只有速度课程允许改变。旧schema3最新运行未加载schema4修正，不能混淆版本。先按v1曝光课程学基础，再按近期恢复发球表现解锁加速，能力不足暂停扩展。
