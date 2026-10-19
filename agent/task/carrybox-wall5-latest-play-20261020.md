---
task_id: "carrybox-wall5-latest-play-20261020"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "录制一下最新ckp play地效果"
development_modes: ["MODEL_DEPLOYMENT"]
allowed_paths: ["docs/carrybox/wall5_latest_play_20261020", "outputs/carrybox/wall5_latest_play_20261020", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-latest-play-20261020.md", "agent/task/carrybox-wall5-latest-play-20261020.md", "agent/report/carrybox-wall5-latest-play-20261020.md", "agent/handoff/carrybox-wall5-latest-play-20261020.md"]
forbidden_scope: ["不修改生产任务、数据、checkpoint或学习配置", "不停止或重启后台训练", "不筛除失败回合或将hold参考起点算成拾箱成功"]
steps: ["核对实时训练、最新完整checkpoint及源码契约", "复用录制工具适配当前rev17，单环境均值动作连续20秒", "严格加载并录制，完整解码及关键帧观察", "保存模型身份、表现及项目记录"]
tests: [{"command": "bash docs/carrybox/wall5_latest_play_20261020/record_and_check.sh"}]
stop_conditions: ["契约/源码身份不一致停止，不以weights-only掩盖差异", "可用显存不足4GiB不启动录制", "失败检查最多范围内修复两次，保留失败工件"]
safeguards: ["仅独立play，不改后台PID254358", "按checkpoint迭代恢复本run课程锚点0，保持深度噪声/物理/终止/RSI", "单环境midpoint配额为loco；记录自动reset及真实episode步数", "原速50Hz控制/25fps视频、时间与深度角标、模型hash可追溯"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

T1既有推理工具运行与局部适配；一条实际录制及视频解码检查。检查对象固定为selection.json所记录最新完整模型，不追逐录制期间新产生的checkpoint。
