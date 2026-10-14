---
task_id: "carrybox-project-layout"
language: "zh-CN"
axes: ["S"]
risk_tier: "T0"
artifact: "TASK"
status: "FROZEN"
original_request: "整理当前项目目录，findbox和football两个任务并列。"
development_modes: ["BUILD_TOOLING"]
allowed_paths: ["README.md", "AGENTS.md", "projects", "agent"]
forbidden_scope: ["移动数据或checkpoint", "更改Gym ID及Python导入", "修改训练实现或启动停止训练", "删除已有改动或历史证据"]
steps: ["核对两项目入口及引用", "统一findbox/football并列目录并保留旧入口", "更新导航及任务归属", "校验链接和保存记录"]
tests: [{"command": "git diff --check"}]
stop_conditions: ["目标目录存在不同内容，无法安全合并"]
safeguards: ["只迁移项目导航目录；旧carrybox入口兼容", "保留已有训练与故障状态快照"]
expert_required: false
device_actions: []
real_device_authorized: false
---

统一项目组织为projects/findbox与projects/football。findbox原始数据路径不变；共享运行代码与资产在根目录source/scripts保留，项目入口记录归属，不复制源码或数据。文档整理不推进此前GPU故障排查，也不改变训练状态。
