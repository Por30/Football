---
task_id: "carrybox-wall5-rev22-comparison-20261022"
language: "zh-CN"
axes: ["L"]
risk_tier: "T0"
allowed_paths: ["docs/carrybox/wall5_rev22_comparison_20261022", "projects/README.md", "projects/findbox/README.md", "docs/carrybox/wall5_training_audit_20261022/README.md", "docs/carrybox/wall5_status_20261022_2338/README.md", "agent/plan/carrybox-wall5-rev22-comparison-20261022.md", "agent/task/carrybox-wall5-rev22-comparison-20261022.md", "agent/report/carrybox-wall5-rev22-comparison-20261022.md", "agent/handoff/carrybox-wall5-rev22-comparison-20261022.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "将 outputs/carrybox/wall5_play4_rev22_20261021 对应训练与当前对比，核实力矩惩罚是否相同；如果相同不能据此归因。"
development_modes: ["ML_TRAINING"]
forbidden_scope: ["不修改生产/数据/模型或训练状态", "不同阶段不作直接退化归因，指标相关性不当作因果"]
steps: ["确认视频模型及两run实际配置/源码身份", "核对力矩、PD和控制配置并比较同迭代日志", "列出实际变更、修正此前归因优先级并更新记录"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_rev22_comparison_20261022/check.py"}]
stop_conditions: ["来源身份不匹配则停止依赖结论", "检查失败最多两次原范围修复，保留证据"]
safeguards: ["只读CPU检查，无额外GPU运行", "保留历史报告并新增有日期的更正"]
expert_required: false
device_actions: []
real_device_authorized: false
---

复核rev22视频对应模型与当前rev26的真实训练配置，针对力矩惩罚归因作证据校准；同轮数对照，不修改训练。
