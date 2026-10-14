---
task_id: "AGILE-V3-AIM035-20260928"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "tests/test_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "docs/agilekickball_v3/README.md", "docs/agilekickball_v3/aim035_20260928", "README.md", "agent/plan/agilekickball-v3-aim035.md", "agent/task/agilekickball-v3-aim035.md", "agent/report/agilekickball-v3-aim035.md", "agent/handoff/agilekickball-v3-aim035.md"]
---

仅调整横向目标空间参数组：最终半宽0.75→0.35m，中点0.50→0.30m，起点0.25m不变。更新v3 revision、现有测试期望与当前说明；历史验证保留。T1由当前Agent直接执行既有回归。
