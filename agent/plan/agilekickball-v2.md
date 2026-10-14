---
task_id: "AGILE-V2-RECOVERY-20260924"
language: "zh-CN"
axes: ["L", "D", "C"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v2.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v2_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "tests/test_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.sh", "docs/agilekickball_v2", "README.md", "agent/plan/agilekickball-v2.md", "agent/task/agilekickball-v2.md", "agent/report/agilekickball-v2.md", "agent/handoff/agilekickball-v2.md"]
---

# AgileKickball v2

实现速度条件恢复包络候选：探索上限保证高速训练机会，已结算联合成功影响练习/挑战采样；恢复在球飞出时并行完成。冻结任务用独立状态机回归及真实CPU仿真冒烟验收，科研假设另见 docs/agilekickball_v2/research_card.json。
