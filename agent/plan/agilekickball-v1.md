---
task_id: "ENG-AGILE-V1-20260921"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball", "scripts/rsl_rl", "tests", "docs/agilekickball_v1", "agent"]
---

新增成功率驱动的AgileKickball-v1，保留v0任务。窗口至少4096已结算球和1024挑战球，两窗口80%且驻留1000步晋级。保持慢球复习和固定1.3–2m距离。冻结2条测试，真实验证16环境不超过1000步、2轮学习更新。
