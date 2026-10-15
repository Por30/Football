---
task_id: "agilekickball-s2s-parity-20261015"
language: "zh-CN"
axes: ["E", "P", "C"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["scripts/sim2sim", "tests/test_kickball_parity.py", "docs/agilekickball_v4/sim2sim_parity_20261015", "projects/football/README.md", "projects/README.md", "agent"]
---

核对所加载v4训练快照与球物理、深度整条输入链路。用真实训练函数做CPU姿态重放，隔离模型几何与计算差异；有证据的小范围错误才修复，未标定接触不盲调。
