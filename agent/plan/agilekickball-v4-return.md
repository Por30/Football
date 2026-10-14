---
task_id: "AGILE-V4-RETURN-20261012"
language: "zh-CN"
axes: ["E", "L", "D"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v4_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v4.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/train_agilekickball_v4.sh", "scripts/rsl_rl/smoke_agilekickball_v4.py", "scripts/rsl_rl/smoke_agilekickball_v4.sh", "tests/test_agilekickball_v4.py", "docs/agilekickball_v4", "logs/rsl_rl/agilekickball_v4", "logs/rsl_rl/agilekickball_v4_smoke", "agent/plan/agilekickball-v4-return.md", "agent/task/agilekickball-v4-return.md", "agent/report/agilekickball-v4-return.md", "agent/handoff/agilekickball-v4-return.md"]
---

基于稳定 v3 新建独立 v4 回传任务；记录本轮发球世界坐标，奖励方向和实际回到目标，宽至窄容差课程。保留 v3 观测/网络、稳定训练设置、恢复和空间边界。从完成的 v3 权重显式初始化，优化器及课程从零开始。单位边界、真实仿真、4096 环境短训通过后后台启动 50000 轮。验收是正确任务语义和运行中的训练，不把短测视为学会精确回传。
