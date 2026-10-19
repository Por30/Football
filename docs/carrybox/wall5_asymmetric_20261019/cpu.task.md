---
task_id: "carrybox-wall5-asymmetric-20261019"
language: "zh-CN"
axes: ["L", "A"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "仅critic改用本体＋机体线速度＋箱子位姿/尺寸真值，独立MLP；actor保持深度＋本体，停止当前wall5并4096环境从零重启。"
development_modes: ["ML_TRAINING"]
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "tests/test_carrybox_asymmetric.py", "docs/carrybox/wall5_asymmetric_20261019", "projects/README.md", "projects/findbox/README.md", "AGENTS.md", "logs/rsl_rl/g1_carrybox_depth/walled5", "agent/plan/carrybox-wall5-asymmetric-20261019.md", "agent/task/carrybox-wall5-asymmetric-20261019.md", "agent/report/carrybox-wall5-asymmetric-20261019.md", "agent/handoff/carrybox-wall5-asymmetric-20261019.md"]
forbidden_scope: ["修改actor输入/网络、深度、AMP、奖励、RSI、碰撞或football/wall3/wall4", "删除旧数据/模型/日志或恢复旧checkpoint替代fresh", "真实硬件动作"]
steps: ["核对在训身份，明确wall5训练专用critic输入和契约", "实现108维当前本体/线速度/箱子局部xyz+rot6/尺寸及独立MLP，修正终止前critic快照", "CPU信息隔离/梯度/超时/导出/恢复回归与4环境真实更新验收", "停止旧wall5保留产物，以4096环境fresh正式启动并核验连续迭代、checkpoint与耗时", "更新项目入口、约定的wall5例外、四工件及证据"]
tests: [{"command": "bash docs/carrybox/wall5_asymmetric_20261019/check.sh"}]
stop_conditions: ["两次范围内修复后测试仍失败", "输入泄漏或非有限输出", "正式训练错误/资源不足则不重复启动"]
safeguards: ["actor只读372维4帧本体和4x27x48深度，辅助监督不变", "critic108维独立MLP不经过CNN；相对位姿以pelvis link坐标系表示，尺寸为箱子局部完整边长米制", "pre-reset终止critic用于timeout bootstrap，其他环境历史不污染", "迁移revision14严格拒绝旧完整resume，原run/model保留", "同用户已授权4096 fresh训练；操作前核对PID命令，非目标进程不操作", "不改变AMP数据/Normalizer/PPO超参/相机/部署actor接口"]
expert_required: true
expert_brief: "docs/carrybox/wall5_asymmetric_20261019/expert_review.md"
device_actions: []
real_device_authorized: false
---


用户本次明确授权仅wall5 critic使用特权状态，覆盖旧无特权critic约定；其余CarryBox与football保持原接口。