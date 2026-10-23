---
task_id: "carrybox-wall5-play4-rev26-20261023"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
allowed_paths: ["docs/carrybox/wall5_play4_rev26_20261023", "outputs/carrybox/wall5_play4_rev26_20261023", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-play4-rev26-20261023.md", "agent/task/carrybox-wall5-play4-rev26-20261023.md", "agent/report/carrybox-wall5-play4-rev26-20261023.md", "agent/handoff/carrybox-wall5-play4-rev26-20261023.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "录制一下最新的ckp play的效果"
development_modes: ["MODEL_DEPLOYMENT"]
forbidden_scope: ["不改生产任务/数据/模型或训练进程", "不选择性裁掉失败，不将RSI持箱/中途拾箱起点计作地面拾箱成功"]
steps: ["锁定最新完整模型13200及源码/训练身份", "复用四相机20秒录像并适配rev26随机reset标注及实际终止原因", "完整解码检查视频、查看关键帧与接触/回合记录", "打包MP4和表现摘要，更新项目记录"]
tests: [{"command": "bash docs/carrybox/wall5_play4_rev26_20261023/record_and_check.sh"}]
stop_conditions: ["源码/模型/契约不匹配即停", "可用显存不足6GiB不运行", "最多两次范围内修复并保留失败证据"]
safeguards: ["4环境默认随机起点、seed42，保留自动reset并逐回合标注", "严格加载、均值动作、恢复checkpoint课程，不训练", "同一物理时刻四宫格，20秒500帧，渲染不推进物理", "既有输出不覆盖，后台训练保持运行"]
expert_required: false
device_actions: []
real_device_authorized: false
---

录制开始检查时最新完整model13200，4环境同步高位视角20秒；按rev26默认随机reset，不强制旧版3loco+1hold。完整保存失败回合和随机起点标签，人工检查关键帧，不修改正式训练。
