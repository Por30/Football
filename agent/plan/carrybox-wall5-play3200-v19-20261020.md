---
task_id: "carrybox-wall5-play3200-v19-20261020"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
allowed_paths: ["docs/carrybox/wall5_play3200_v19_20261020", "outputs/carrybox/wall5_play3200_v19_20261020", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-play3200-v19-20261020.md", "agent/task/carrybox-wall5-play3200-v19-20261020.md", "agent/report/carrybox-wall5-play3200-v19-20261020.md", "agent/handoff/carrybox-wall5-play3200-v19-20261020.md"]
artifact: "PLAN"
status: "FROZEN"
---

复用既有录制工具，固定最新完整rev19模型，以原训练课程、噪声和物理参数做20秒单环境均值动作回放。严格核对契约与权重，视频完整解码并检查关键帧。仅生成视频/记录，不修改生产代码或停止训练；单起点表现不代替成功率评估。
