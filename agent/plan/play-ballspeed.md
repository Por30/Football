---
task_id: "ENG-PLAY-BALLSPEED-20260921"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["scripts/rsl_rl/play.py", "scripts/rsl_rl/cli_args.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_state.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v1.py", "tests/test_play_ballspeed.py", "docs/agilekickball_v1", "agent"]
---

新增play可选--ballspeed MIN MAX，单位m/s，显式范围覆盖课程/阶段混合采样，从首球起持续生效。未传参行为不变。
