---
task_id: "carrybox-wall4-depth-timing-audit"
language: "zh-CN"
axes: ["P"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["scripts/rsl_rl/summarize_carrybox_timing.py", "docs/carrybox/depth_timing_20261014", "agent", "projects/findbox/README.md", "projects/README.md"]
original_request: "用户提供X2 Warp深度流程，建议先实测物理、深度及PPO耗时；核对当前G1与该说明的差异。"
development_modes: ["BUILD_TOOLING"]
forbidden_scope: ["修改训练配置、观测或teacher/student方案", "启动停止重启正式训练", "将已有profile称为本轮新GPU测量"]
steps: ["核对G1实际backend和当前进程", "校验profile对应源码hash，汇总分项与日志计时", "保存证据及局限，更新项目记录"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python scripts/rsl_rl/summarize_carrybox_timing.py"}]
safeguards: ["只读当前进程和日志，不占用训练GPU", "嵌套profile累计时间不可相加；不将host profile视为CUDA kernel独立时间", "保留actor/critic无特权约定"]
stop_conditions: ["源码hash不匹配或profile缺失则拒绝外推当前训练", "失败只允许两次范围内修复"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

复用上一轮真实4096测量及新正式日志，仅整理分项证据；没有中断训练或迁移传感器。X2结构来自用户说明，当前G1以本地实现和运行参数为准。
