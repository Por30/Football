---
task_id: "carrybox-wall5-headfix-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_reward_geometry.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "tests/test_carrybox_reward_geometry.py", "docs/carrybox/wall5_headfix_20261021", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-headfix-20261021.md", "agent/task/carrybox-wall5-headfix-20261021.md", "agent/report/carrybox-wall5-headfix-20261021.md", "agent/handoff/carrybox-wall5-headfix-20261021.md"]
original_request: "你先检查一下 是否正确 把正确的版本修后 重新启动训练。核对X2头高锚点1.112；修正0.439/0.878/0.933及指数7.29；去掉early_failure；分别记录骨盆/头高终止。"
development_modes: ["SYSTEM_TUNING", "ML_TRAINING"]
forbidden_scope: ["不修改足球、机器人资产、数据集、AMP/PPO/观测架构或RSI比例", "不处理尚无因果证据的站位距离与膝碰撞", "不恢复旧checkpoint、不删除旧数据或操作其他任务进程"]
steps: ["核对标定来源、有效代码和当前训练身份", "修正头高参数、移除惩罚、拆分终止并保留legacy统计兼容", "运行CPU边界回归及20环境PPO/AMP与checkpoint集成短测", "通过后停止旧训练，以4096环境/seed42/40000轮从头启动", "核对持续更新、正式配置及每轮6秒目标，更新项目和工程记录"]
tests: [{"command": "bash docs/carrybox/wall5_headfix_20261021/validate_and_restart.sh"}]
stop_conditions: ["CPU或短测失败不停止旧训练；失败仅允许两次范围内修复", "源码/数据身份变化、旧PID身份不符或显存不足停止启动", "新训练非有限/契约不符不验收；已启动后不重复启动"]
safeguards: ["仅wall5选择修正后的奖励几何和拆分终止；wall3/4 legacy不变", "头高沿用G1物理head COM，原始标定文件和资产hash可追溯", "终止在reset前计算，union不重复计数；timeout语义保持", "移除early_failure同时修复依赖它的日志索引；新契约revision20严格拒绝旧配方恢复", "新模型检查独立critic108与深度actor、AMP60、全新优化器/归一化状态", "单学习轴T2；仅改变学习任务参数/终止及监测，无资产/硬件或感知管线修改，无需专家"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

核对用户更正，将 wall5 头高标定改为 X2 1.112 m，移除 early_failure，将低骨盆和低头终止分开记录。保持骨盆/箱子标定、3D距离、RSI75/5/20、roll0.5及其他训练配置。验证后停止身份匹配的旧进程，新建4096环境正式run从头训练，保留全部旧模型与日志。X2数字如无本地资产只能注明用户提供，不能冒称独立FK验证。
