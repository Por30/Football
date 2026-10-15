---
task_id: "agilekickball-ball-speed"
language: "zh-CN"
axes: ["C"]
risk_tier: "T1"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["scripts/sim2sim", "tests/test_kickball_ball_speed.py", "docs/agilekickball_v4/sim2sim_20261014", "projects/football/README.md", "projects/README.md", "agent"]
---

在现有深度窗口增加球速滑块、立即应用与重新发球。控制步开始消费UI事件，显示设定值及实际水平速度；仅变更球状态。
