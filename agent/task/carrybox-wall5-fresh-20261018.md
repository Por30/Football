---
task_id: "carrybox-wall5-fresh-20261018"
language: "zh-CN"
axes: ["A"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "不用恢复 你重新i启动就行了"
development_modes: ["BUILD_TOOLING"]
allowed_paths: ["docs/carrybox/wall5_fresh_20261018", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-fresh-20261018.md", "agent/task/carrybox-wall5-fresh-20261018.md", "agent/report/carrybox-wall5-fresh-20261018.md", "agent/handoff/carrybox-wall5-fresh-20261018.md"]
forbidden_scope: ["修改生产源码/配置/数据", "删除历史模型或日志", "恢复或warm-start旧checkpoint", "操作无关训练/实机"]
steps: ["只读核验当前wall5及资源", "停止恢复运行，按当前配置从零启动4096正式wall5", "核验fresh配置、首checkpoint优化器步数与连续训练，更新记录"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_fresh_20261018/verify.py"}]
stop_conditions: ["启动失败或契约/新初始化证据不符则停止完成声明并排查", "资源冲突时不并发额外训练"]
safeguards: ["用户明确要求fresh；命令不得含resume/checkpoint/warm_start", "保留全部历史模型/日志，不改优化后的学习及物理配置", "只停止身份匹配的当前wall5，确认退出后启动", "启动成功不等于收敛；先确认实际迭代再报告"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

本次仅操作授权的wall5正式训练与记录；复用已通过的工程实现，不重复仿真验收。
