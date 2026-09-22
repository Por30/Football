---
task_id: "ENG-AGILE-V1-REWARD-20260922"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["SYSTEM_TUNING", "ML_TRAINING"]
original_request: "同时提高一下踢球的奖励 减少站着不情况现现"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v1_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/rewards.py", "tests/test_agilekickball_rewards.py", "scripts/rsl_rl/smoke_agilekickball_v1.py", "scripts/rsl_rl/smoke_agilekickball_v1.sh", "docs/agilekickball_v1", "agent"]
forbidden_scope: ["改课程/状态转换/v0配置/PPO/AMP/网络/深度监督", "长训练/用户进程控制/真实设备"]
steps: ["冻结奖励前后值与实际dt尺度", "增加相位站立函数并仅在v1配置新权重", "验证相位、原pulse一次性、奖励排序及真实PPO更新", "更新说明与工程回执"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_rewards.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v1.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v1.sh"}]
stop_conditions: ["超出奖励调参范围", "失败修复超过两轮"]
safeguards: ["v0奖励函数与配置行为不变；站立helper无状态写入", "保留kickball_tick权重非零，pulse不改变时序且终止无kick奖金", "新奖励保留原dt缩放与AMP混合，不把配置权重当单次实际奖励", "有球未踢出降站立，踢出/恢复保留站立；不惩罚恢复期静止", "不因本次奖励变化声称已解决站立局部最优；碰撞代理仍可包含被动反弹", "原smoke的rewards与v0完全相等断言被用户新需求取代，改为新权重逐项与其余项不变检查"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

在现有简单速度v1上仅调奖励：kick bonus60→300，return4→8，miss−15→−60，face0.5→0.2；站立原函数乘相位系数，ball_active且未踢出时0.25，其余1。approach不加权，避免把球自行靠近误当主动动作。课程、reset、AMP/PPO、网络与深度监督均保持。原代理击球判据不等于主动踢球，本次不增加复杂成功门槛。T2单L轴奖励调参，当前Agent直接执行，无需专家。
