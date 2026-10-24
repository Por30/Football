---
task_id: "carrybox-wall11-start24-20261024"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "停掉当前训练 启动wall11训练"
allowed_paths: ["docs/carrybox/wall11_start24_20261024", "logs/rsl_rl/g1_carrybox_depth/walled11", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall11-start24-20261024.md", "agent/task/carrybox-wall11-start24-20261024.md", "agent/report/carrybox-wall11-start24-20261024.md", "agent/handoff/carrybox-wall11-start24-20261024.md"]
forbidden_scope: ["修改生产代码/数据或其他任务", "删除或覆盖旧训练模型和日志", "从docs验证模型初始化正式训练", "停止未识别的无关进程"]
development_modes: ["ML_TRAINING"]
steps: ["核对实际进程、最新wall10模型、wall11已通过的验收和GPU资源", "核验PID身份后停止wall10，确认退出释放显存", "启动独立wall11正式fresh run并记录PID和日志", "检查实际4096×24参数、连续迭代、有限值与首模型，更新项目记录"]
tests: [{"command": "bash docs/carrybox/wall11_start24_20261024/check.sh"}]
stop_conditions: ["GPU资源冲突或旧进程身份不符", "启动失败/非有限值或物理错误", "两次范围内修复后验收仍失败"]
safeguards: ["只停止已核对的wall10 PID2402395，保留已保存checkpoint", "wall11从零初始化，不严格resume或隐式warm start wall10", "保持4096环境、24步、5×4、seed42及已验证噪声/墙柱", "正式产物仅新建walled11 run；状态核验不等于收敛评估"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

用户已明确授权停止当前训练并启动wall11。T1单学习轴操作，复用已验证实现，不再运行额外GPU smoke。
