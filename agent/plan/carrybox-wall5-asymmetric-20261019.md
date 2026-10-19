---
task_id: "carrybox-wall5-asymmetric-20261019"
language: "zh-CN"
axes: ["L", "A"]
risk_tier: "T2"
artifact: "PLAN"
status: "READY"
---

wall5采用非对称AC：actor保留372维本体和4帧深度；critic当前93维本体＋3维pelvis线速度＋3维箱位置＋6维相对旋转＋3维箱尺寸，共108维，独立512/256/256 MLP。CPU和仿真验证后停止旧训练，4096环境fresh启动，记录新旧身份与有限更新。
