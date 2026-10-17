---
task_id: "carrybox-wall5-length-20261016"
language: "zh-CN"
axes: ["E", "P", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "READY"
allowed_paths: ["docs/carrybox/wall5_length_20261016", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-length-20261016.md", "agent/task/carrybox-wall5-length-20261016.md", "agent/report/carrybox-wall5-length-20261016.md", "agent/handoff/carrybox-wall5-length-20261016.md"]
---

用户要求排查当前wall5平均回合长度停滞。核查已运行的wall5，而非未正式训练的足球v5。仅新增隔离的诊断脚本/记录，不修改生产代码或停止重启训练。先解析固定截至7249轮日志及model_7200，再16环境进行采样/确定性动作与有/无push的四组各1200步推理，记录终止前姿态及分技能行为。保持无特权观测、原深度、RSI、其他随机化和checkpoint加载校验。验收是证据支持的诊断，不承诺通过短回放证明长期因果或收敛。
