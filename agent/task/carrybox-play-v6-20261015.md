---
task_id: "carrybox-play-v6-20261015"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
allowed_paths: ["scripts/rsl_rl/play.py", "docs/carrybox/play_v6_20261015", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-play-v6-20261015.md", "agent/task/carrybox-play-v6-20261015.md", "agent/report/carrybox-play-v6-20261015.md", "agent/handoff/carrybox-play-v6-20261015.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "给指定model_14000.pt用4个环境play的命令"
development_modes: ["ML_TRAINING"]
forbidden_scope: ["修改训练或checkpoint", "停止/启动正式训练", "默认绕过恢复契约"]
steps: ["核对播放契约", "新增显式仅权重播放分支", "CPU验证及提供命令"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/play_v6_20261015/check.py"}]
stop_conditions: ["需修改模型结构或数据", "检查失败两次"]
safeguards: ["默认load继续严格契约检查", "显式选项限CarryBox并复用warm_start的shape/finite校验", "只提供播放命令，不启动GPU仿真"]
expert_required: false
device_actions: []
real_device_authorized: false
---

旧revision6策略在当前revision7环境中显式仅权重播放；不声称复现原始环境。
