---
task_id: "carrybox-wall10-perf-20261023"
language: "zh-CN"
axes: ["L", "P"]
risk_tier: "T2"
artifact: "PLAN"
status: "READY"
---

保持wall10训练/感知语义，参照本地深度与学习优化，核对4096×100与历史4096×24的工作量差异，减少更新同步与碎片计算；真实GPU前后计时。历史正式进程已退出，仅运行docs下验证。
