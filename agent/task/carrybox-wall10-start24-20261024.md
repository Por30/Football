---
task_id: "carrybox-wall10-start24-20261024"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["docs/carrybox/wall10_start24_20261024", "logs/rsl_rl/g1_carrybox_depth/walled10", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall10-start24-20261024.md", "agent/task/carrybox-wall10-start24-20261024.md", "agent/report/carrybox-wall10-start24-20261024.md", "agent/handoff/carrybox-wall10-start24-20261024.md"]
development_modes: ["ML_TRAINING"]
original_request: "按照24步的 你启动wall10 训练 然后给我看训练日志的命令"
forbidden_scope: ["修改生产源码和其他任务", "停止现有训练或覆盖旧模型", "使用验证checkpoint初始化正式训练"]
steps: ["核对实际资源与启动配置", "使用24步CLI覆盖启动独立正式fresh训练", "核对进程、实际参数、迭代耗时和首个checkpoint", "更新项目入口与启动证据，提供实时日志命令"]
tests: [{"command": "bash docs/carrybox/wall10_start24_20261024/check.sh"}]
stop_conditions: ["GPU资源冲突", "启动失败或出现非有限值"]
safeguards: ["保持4096环境、5x4更新、seed42及其他既有wall10训练细节", "只创建新run，旧100步checkpoint原样保留", "不以启动正常代表收敛或独立评估通过"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

本任务授权正式训练启动。验收为后台进程持续推进、实际24步参数和首个模型身份一致；不启动额外仿真。
