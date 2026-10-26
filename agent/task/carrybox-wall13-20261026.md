---
task_id: "carrybox-wall13-20261026"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "新增wall13 amp数据集换成我修改后的数据集 搬起箱子后稳定站着的版本 其他不变"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall13_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall13.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/play_carrybox_walled.sh", "docs/carrybox/wall13_20261026", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall13-20261026.md", "agent/task/carrybox-wall13-20261026.md", "agent/report/carrybox-wall13-20261026.md", "agent/handoff/carrybox-wall13-20261026.md"]
forbidden_scope: ["改动wall12及以前任务、足球生产模块、共享CNN/AMP/资产或现有数据文件", "启动正式训练、停止或重启已有进程", "修改AMP权重、RSI、观测、辅助监督、奖励、PPO参数或部署接口"]
development_modes: ["ML_TRAINING"]
steps: ["核对用户修改数据与wall12实际checkpoint并记录相同版本事实", "新增wall13独立配置、环境契约、注册与shell入口", "执行数据/配置及16环境24步一次更新与恢复定向检查", "更新项目入口、总看板和工程交接"]
tests: [{"command": "bash docs/carrybox/wall13_20261026/validate.sh"}]
stop_conditions: ["两次范围内修复后检查仍失败", "用户指明尚未可访问的其他数据集", "GPU可用显存不足6000MiB或需要停止已有进程"]
safeguards: ["数据选择为assets/motions/findbox revision3 findbox_hold_v1_named；若用户提供另一路径需先核实后更新合同", "数据文件/manifest/文件名映射保持原样，现有加载器继续检查所有clip哈希", "wall12继承关系保持全部物理/奖励/深度噪声/位姿监督和4096x24、5x4配置", "独立variant及日志目录，禁止旧wall12模型严格恢复成wall13", "只做16环境短测，检查现有训练PID不退出，不启动正式wall13训练"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

按用户“其他不变”限定为任务入口和数据选择配置。当前匹配的静止持箱版本已经用于wall12，wall13不制造虚假的数据差异；本次不改数据、manifest或映射。冻结一条实际仿真定向检查，测试产物只落docs。
