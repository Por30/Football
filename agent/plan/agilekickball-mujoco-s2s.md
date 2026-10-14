---
task_id: "agilekickball-mujoco-s2s"
language: "zh-CN"
axes: ["E", "P", "C", "L", "S"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["unitree_mujoco", "unitree_rl_lab", "perceptual_ball/scripts/sim2sim", "perceptual_ball/tests/test_kickball_mujoco.py", "perceptual_ball/docs/agilekickball_v4/sim2sim_20261014", "perceptual_ball/agent", "perceptual_ball/projects/football/README.md", "perceptual_ball/projects/README.md", "perceptual_ball/README.md"]
---

更新两个官方仓库main并保留本地Go2定制，编译G1控制器；新增独立CPU v4解析深度s2s。以接口测试及500步MuJoCo闭环验收实现，策略跌倒/技能结果独立记录。本任务路径基准为/home/cao；测试工作目录为/home/cao/perceptual_ball。
