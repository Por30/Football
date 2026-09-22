---
task_id: "ENG-G1-SOCCER-AUDIT-20260919"
artifact: "PLAN"
status: "DRAFT"
language: "zh-CN"
axes: ["L", "P", "D", "C"]
risk_tier: "T1"
allowed_paths: ["docs/research/iros2027", "agent"]
---

# G1 Soccer v2 审查计划

用户已确认 G1。本轮审查当前 Soccer v2 可改进处，以源码、已有 checkpoint 和 CPU 离线反例区分确定缺陷与待验证设计问题。验收为给出按优先级排序的具体位置、影响、建议与证据；不要求在本轮修复训练实现。

只新增审查文档与离线探针，并更新平台记录。保留用户现有代码、训练产物与实验条件；不启动仿真、训练或实机。T1 为离线审查风险，非后续训练代码修复风险。
