---
task_id: "carrybox-wall5-loco-fix-20261019"
language: "zh-CN"
axes: ["E", "C", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "READY"
---

从rev15增量推扰和摩擦基线修复loco训练：保障实际环境步数80/0/20、用可验证的G1静止起点引入运动RSI课程、针对物理目标范围施加可导正则并限制std上升。保持任务和观察边界，验收后从头正式启动4096环境；稳定行走和完整拾箱需后续学习评估。
