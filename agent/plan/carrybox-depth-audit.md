---
task_id: "carrybox-depth-audit"
language: "zh-CN"
axes: ["P"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["scripts/audit_g1_depth.py", "scripts/audit_g1_depth.sh", "docs/carrybox/depth_audit", "projects/findbox/README.md", "projects/football/README.md", "projects/README.md", "agent"]
---

只审计深度感知路径。FindBox使用真实RTX传感器，足球现有解析球面管线不含其他物体遮挡。以资产转换记录的PhysHSI G1 URDF作为模型依据，对比本地Unitree URDF版本；实机配置路径已向用户询问。使用静态渲染及有限reset检查，避免重跑已知失败的PPO长链路。
