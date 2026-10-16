---
task_id: "carrybox-play-oom-20261016"
language: "zh-CN"
axes: ["S"]
risk_tier: "T1"
allowed_paths: ["scripts/rsl_rl/play_carrybox_walled.sh", "docs/carrybox/play_oom_20261016", "README.md", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-play-oom-20261016.md", "agent/task/carrybox-play-oom-20261016.md", "agent/report/carrybox-play-oom-20261016.md", "agent/handoff/carrybox-play-oom-20261016.md"]
artifact: "PLAN"
status: "READY"
---

显存OOM发生在环境初始化、模型加载之前。仅新增1–4环境小规模播放配方，降低PhysX预分配pair容量和GUI尺寸；不改变训练或观测。T1局部启动配置，无需专家。
