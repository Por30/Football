---
task_id: "AGILE-V2-STABILITY-AUDIT-20260924"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
development_modes: ["SYSTEM_TUNING"]
original_request: "你看一下当前v2 和v1 的表现 v2 不稳定很多 是你那些改动的原因造成的"
allowed_paths: ["docs/agilekickball_v2/stability_audit_20260924", "agent/plan/agilekickball-v2-stability-audit.md", "agent/task/agilekickball-v2-stability-audit.md", "agent/report/agilekickball-v2-stability-audit.md", "agent/handoff/agilekickball-v2-stability-audit.md"]
forbidden_scope: ["修改训练生产代码或当前运行参数", "终止或重启用户训练", "启动新长训练", "把短推理回放当从零训练因果消融"]
steps: ["读取现有训练指标及保存配置", "相同推理条件下对照恢复规则与发球距离", "记录结论、反例和修正建议"]
tests: [{"command": "bash docs/agilekickball_v2/stability_audit_20260924/run_replay.sh"}]
stop_conditions: ["诊断需要修改生产代码或中止用户训练", "有界CPU回放超过300秒"]
safeguards: ["仅CPU16环境，3策略×3条件×800步", "不更新策略参数，不使用GPU训练资源", "日志终止标签是最近终止类型占比，不冒充真实终止计数；回放只在done时统计", "同轮数比较为主，相近球速的成熟v1只作补充", "仅对可观测现象下结论，因果归因需训练消融"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

# v2稳定性只读审计

比较已冻结日志快照与相同速度/距离下的策略回放，检查加速课程和恢复规则的作用；不改动正在运行的训练。工程只读诊断按T1执行，无专家改代码。
