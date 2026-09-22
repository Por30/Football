---
task_id: "ENG-AGILE-V1-REWARD-20260922"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v1_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/rewards.py", "tests/test_agilekickball_rewards.py", "scripts/rsl_rl/smoke_agilekickball_v1.py", "scripts/rsl_rl/smoke_agilekickball_v1.sh", "docs/agilekickball_v1", "agent"]
---

在现有简单速度v1上仅调奖励：kick bonus60→300，return4→8，miss−15→−60，face0.5→0.2；站立原函数乘相位系数，ball_active且未踢出时0.25，其余1。approach不加权，避免把球自行靠近误当主动动作。课程、reset、AMP/PPO、网络与深度监督均保持。原代理击球判据不等于主动踢球，本次不增加复杂成功门槛。T2单L轴奖励调参，当前Agent直接执行，无需专家。
