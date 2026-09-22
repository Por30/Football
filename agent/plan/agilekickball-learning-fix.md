---
task_id: "ENG-AGILE-LEARNING-20260920"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball", "scripts/rsl_rl", "tests", "docs/agilekickball", "agent"]
---

修复零发球与KL拒绝误报零误差。首球近距离引导逐步恢复常规距离；局内保持严格恢复。验收CPU边界、真实仿真训练和独立样本误差；预算不超过128环境/100轮或15分钟训练。
