---
task_id: "ENG-AGILE-V1-SIMPLE-SPEED-20260922"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v1.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v1_env_cfg.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "tests/test_agilekickball_v1.py", "tests/test_play_ballspeed.py", "scripts/rsl_rl/smoke_agilekickball_v1.py", "scripts/rsl_rl/smoke_agilekickball_v1.sh", "docs/agilekickball_v1", "agent"]
---

重新以 AgileKickball-v0 的近距离起步、来球曝光课程与连续球回合构建 v1。前240000平均来球控制步保持v0速度上限0.8→2，后240000步2→5；全程下限0.4。无成功率门槛、挑战混合或新奖励。v1恢复门控仅移除全身瞬时关节速度RMS，保留身体姿态/速度/脚位与连续稳定时间、超时和终止优先。保留v0源文件和训练算法。验收覆盖端点、空等不升级、均值与重复tick、真实新策略PPO更新、随机探索下连续重发、checkpoint冻结与play覆盖。长期踢球能力不由短smoke代证。
