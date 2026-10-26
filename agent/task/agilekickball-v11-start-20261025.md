---
task_id: "agilekickball-v11-start-20261025"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "完成后直接启动kickball11正式练练"
allowed_paths: ["docs/kickball_v11/start_20261025", "docs/kickball_v11/README.md", "projects/README.md", "projects/football/README.md", "logs/rsl_rl/agilekickball_v4/kickballv11", "agent/plan/agilekickball-v11-start-20261025.md", "agent/task/agilekickball-v11-start-20261025.md", "agent/report/agilekickball-v11-start-20261025.md", "agent/handoff/agilekickball-v11-start-20261025.md"]
forbidden_scope: ["修改任务参数、其他任务源码、数据或既有模型", "停止或重启其他进程", "实机操作"]
development_modes: ["ML_TRAINING"]
steps: ["只读复核实际进程、资源、已有测试和正式配方", "独立新run从零启动4096环境24步20000轮seed42正式训练", "核验首模型schema/课程/AMP/辅助头与优化器以及至少12轮持续进展", "更新项目状态与工程回执，保持正式训练后台运行"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/kickball_v11/start_20261025/verify_start.py"}]
stop_conditions: ["正式进程退出或出现非有限数值/CUDA错误", "资源不足或需要操作他人进程", "需超出既有配方修改生产代码"]
safeguards: ["新run从零启动，不将docs短测模型作为正式初始化", "保留5m/s上限、无墙柱、站姿reset、actor真值隔离与辅助头", "正式产物仅写logs/rsl_rl/agilekickball_v4/kickballv11，PID和迭代数注明日期"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

本次用户授权取代此前实现任务“未启动正式长训”的操作范围。采用现有训练脚本启动并验证，不再运行额外GPU短测。
