---
task_id: "carrybox-wall10-play4-20261024-0124"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["docs/carrybox/wall10_play4_20261024_0124", "outputs/carrybox/wall10_play4_20261024_0124", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall10-play4-20261024-0124.md", "agent/task/carrybox-wall10-play4-20261024-0124.md", "agent/report/carrybox-wall10-play4-20261024-0124.md", "agent/handoff/carrybox-wall10-play4-20261024-0124.md"]
original_request: "录制一下最新wall10 ckp play的效果"
development_modes: ["MODEL_DEPLOYMENT"]
forbidden_scope: ["修改生产任务/模型/数据", "停止或重启正式训练", "筛掉失败或把参考持箱称为地面拾箱"]
steps: ["锁定最新完整checkpoint、源码和实际训练进程", "复用既有四相机录制，严格核对wall10契约和权重", "录制20秒并完整解码，检查关键帧与行为数据", "交付视频并更新项目和工程记录"]
tests: [{"command": "bash docs/carrybox/wall10_play4_20261024_0124/record_and_check.sh"}]
stop_conditions: ["契约或权重不一致", "可用显存不足6GiB", "两次范围内修复后检查仍失败"]
safeguards: ["4环境seed42均值动作，保留随机reset、本体噪声、物理随机化和力脉冲", "新输出路径，全部失败和reset保留；渲染不推进物理", "训练进程保持；单次4环境录像不代表总体成功率"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

在选择时间锁定model_1000，继承已验证录制布局；仅适配wall10状态与指标，不更改生产任务。
