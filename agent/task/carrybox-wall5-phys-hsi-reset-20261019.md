---
task_id: "carrybox-wall5-phys-hsi-reset-20261019"
language: "zh-CN"
axes: ["L", "C"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "可以参考本地phsi项目 看一他的的reset逻辑"
development_modes: ["SIMULATOR_EXTENSION"]
allowed_paths: ["docs/carrybox/wall5_physhsi_reset_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-phys-hsi-reset-20261019.md", "agent/task/carrybox-wall5-phys-hsi-reset-20261019.md", "agent/report/carrybox-wall5-phys-hsi-reset-20261019.md", "agent/handoff/carrybox-wall5-phys-hsi-reset-20261019.md"]
forbidden_scope: ["不修改 PhysHSI、本项目生产源码、数据、模型或运行配置", "不启动GPU仿真、不停止或重启训练", "不从代码差异声称已确认失稳因果或收敛"]
steps: ["读取实际注册任务、配置和reset/motionlib调用链", "对照wall5速度、采样、接地、动作缓存和终止逻辑", "CPU核对源码身份与RSI数据速度尺度", "记录结论与适用边界并更新项目入口"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_physhsi_reset_20261019/check.py"}]
stop_conditions: ["源码身份变更或数据校验失败时停止结论，保留现场", "核验失败最多两次范围内修正；不得扩展至GPU或修改生产"]
safeguards: ["四元数顺序/坐标系及m/s、rad/s分别注明", "区分默认配置、resume变体和真实运行证据", "保留训练进程及全部已有改动"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

T1 只读对照；一个 CPU 检查保存来源哈希、配置归一化比例、参考轨迹速度和训练进程快照。
