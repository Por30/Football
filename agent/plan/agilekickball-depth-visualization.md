---
task_id: "agilekickball-depth-visualization"
language: "zh-CN"
axes: ["P"]
risk_tier: "T1"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["scripts/sim2sim/kickball_mujoco.py", "scripts/sim2sim/depth_visualization.py", "docs/agilekickball_v4/sim2sim_20261014", "projects/football/README.md", "projects/README.md", "agent"]
---

为现有MuJoCo runner增加只读深度采集出口，生成真实策略输入的米制深度图、八帧历史、MP4和NPZ。图像颜色范围固定，保留原始27x48像素；不改控制/训练/模型。T1局部可视化，无专家。
