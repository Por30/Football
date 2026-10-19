---
task_id: "carrybox-wall5-loco-early-20261019"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "READY"
---

目标是定位空手行走起点前20步即倾倒的原因。严格恢复rev14 model11200，以同初态策略/参考角/默认角/参考轨迹/清初速保持参考角做五组短测，再核对分技能正式日志与动作链。只在docs编写诊断器并更新项目记录；不修改生产配方或重启训练。验收为CPU与GPU两条冻结检查通过、证据能区分策略加速失稳和未排除的控制适配问题。
