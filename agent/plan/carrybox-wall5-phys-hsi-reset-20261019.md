---
task_id: "carrybox-wall5-phys-hsi-reset-20261019"
language: "zh-CN"
axes: ["L", "C"]
risk_tier: "T1"
artifact: "PLAN"
status: "READY"
---

核对本地 PhysHSI carrybox 与当前 wall5 revision17 的 reset 调用链、混合比例、速度与缓存语义及终止条件。限定只读代码/CPU 数据审计，保存带源码身份的对照；不修改运行配置或操作训练。验收是一次 CPU 核验及四工件一致性，不把代码差异当作摔倒因果证据。
