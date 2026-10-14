---
task_id: "AGILE-V2-STABILITY-FIX-20260924"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v2.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v2_env_cfg.py", "tests/test_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.sh", "docs/agilekickball_v2", "README.md", "agent/plan/agilekickball-v2-stability-fix.md", "agent/task/agilekickball-v2-stability-fix.md", "agent/report/agilekickball-v2-stability-fix.md", "agent/handoff/agilekickball-v2-stability-fix.md"]
---

# v2稳定性修正

基于9条件CPU回放与训练日志修正早期距离、固定恢复和奖励错配；已停止旧进程，保留6m/s覆盖，不自动启动用户长训练。旧契约与结果在stability_fix_20260924/before归档。
