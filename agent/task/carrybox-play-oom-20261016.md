---
task_id: "carrybox-play-oom-20261016"
language: "zh-CN"
axes: ["S"]
risk_tier: "T1"
allowed_paths: ["scripts/rsl_rl/play_carrybox_walled.sh", "docs/carrybox/play_oom_20261016", "README.md", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-play-oom-20261016.md", "agent/task/carrybox-play-oom-20261016.md", "agent/report/carrybox-play-oom-20261016.md", "agent/handoff/carrybox-play-oom-20261016.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "用户贴出model_21600播放日志：Warp CUDA error 2 out of memory，Failed to allocate 763776 bytes on cuda:0；排查并提供可用播放命令。"
development_modes: ["SYSTEM_TUNING", "BUILD_TOOLING"]
forbidden_scope: ["停止或重启正式训练", "修改物理任务/碰撞/相机或checkpoint契约", "更改原模型", "增加无关功能"]
steps: ["核对日志、实际GPU资源与播放路径", "新增小规模wall播放配方，仅调整容量和GUI尺寸", "用真实checkpoint在已有训练并行时GUI有限播放验证", "记录原因、验证限制与启动命令"]
tests: [{"command": "bash docs/carrybox/play_oom_20261016/validate.sh"}]
stop_conditions: ["同一测试两次修复仍失败", "需要停止既有训练才可继续", "PhysX容量溢出或非有限状态"]
safeguards: ["正式训练保持不动", "保持真实Warp深度、身体遮挡与严格checkpoint加载", "低容量配方限制1至4环境", "验证模型及导出只写docs；测试完成清理本次进程", "GUI设置只改显示尺寸，策略相机48×27不变"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

显存OOM发生在环境初始化、模型加载之前。仅新增1–4环境小规模播放配方，降低PhysX预分配pair容量和GUI尺寸；不改变训练或观测。T1局部启动配置，无需专家。
