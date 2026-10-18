---
task_id: "carrybox-wall5-ground-20261017"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "READY"
---

wall5使用独立地面拾箱数据profile，旧15段与其他任务不动。箱子全部贴地reset，取消hold RSI和平台，pickup仅离地前帧。保留全身碰撞及原策略接口；两条命令验证数据、完整reset和小规模PPO/AMP更新恢复。可选澄清未收到答复，已明示按完整地面起点轨迹处理；仅新增可逆profile，未将未回复记为确认。
