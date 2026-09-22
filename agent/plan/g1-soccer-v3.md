---
task_id: "ENG-G1-SOCCER-V3-20260919"
language: "zh-CN"
axes: ["E", "P", "C", "L", "D", "S"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball", "scripts/rsl_rl", "tests", "docs/research/iros2027", "agent"]
---

修复审查中的确定错误，新增独立 G1 Soccer v3，保留旧任务注册与旧 checkpoint 文件。验收覆盖 AMP 特征、terminal transition、保存加载、接触与完整回合、时序感知、完整导出及最小真实仿真更新；不承诺训练性能。
