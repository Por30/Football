---
task_id: "carrybox-wall5-play4-rev22-20261022-1204"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["docs/carrybox/wall5_play4_rev22_20261022_1204", "outputs/carrybox/wall5_play4_rev22_20261022_1204", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-play4-rev22-20261022-1204.md", "agent/task/carrybox-wall5-play4-rev22-20261022-1204.md", "agent/report/carrybox-wall5-play4-rev22-20261022-1204.md", "agent/handoff/carrybox-wall5-play4-rev22-20261022-1204.md"]
original_request: "看一下最新的play效果"
development_modes: ["MODEL_DEPLOYMENT"]
forbidden_scope: ["不改生产任务、模型、数据或学习参数", "不停止或重启后台训练", "不筛选失败回合，不把持箱参考起点当成拾箱成功"]
steps: ["锁定最新完整模型及正式进程/源码身份", "复用四相机同步回放脚本，适配revision22契约及米制角标", "录制20秒并完整解码、核对起点reset和关键帧", "保存可观看MP4、表现记录及项目入口"]
tests: [{"command": "bash docs/carrybox/wall5_play4_rev22_20261022_1204/record_and_check.sh"}]
stop_conditions: ["契约或源码/模型身份不一致即停，不绕过严格加载", "可用显存不足6GiB不运行", "范围内最多修复两次并保留失败记录"]
safeguards: ["严格完整契约和权重加载，按checkpoint恢复yaw/push课程", "旁观相机不影响actor或物理时间，全部4格同一物理时刻", "米制深度仅显示时除3；策略输入仍为原始米值", "4环境50Hz控制/25fps录制500帧，3loco和1hold起点清晰标注", "后台训练继续；不覆盖历史产物，记录开始和结束进程身份"]
expert_required: false
device_actions: []
real_device_authorized: false
---

按最新请求录制当前最新完整checkpoint，沿用用户此前偏好的4机器人、高位旁观相机和20秒MP4。独立play严格加载revision22；修正录像深度角标对米制输入的显示映射，不改变actor深度。四环境按默认配额3loco+1hold；标注持箱起点，完整保留失败/reset。检查完整解码、关键帧、模型/源码及后台训练身份。
