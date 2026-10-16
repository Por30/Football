---
task_id: "agilekickball-s2s-scene-depth-20261016"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "DONE"
allowed_paths: ["scripts/sim2sim/kickball_mujoco.py", "scripts/sim2sim/scene_depth.py", "scripts/sim2sim/depth_visualization.py", "scripts/sim2sim/audit_kickball_parity.py", "scripts/sim2sim/diagnose_kickball_speed.py", "tests/test_kickball_scene_depth.py", "tests/test_kickball_parity.py", "source/perceptual_ball/perceptual_ball/kickball_depth.py", "docs/agilekickball_v5/sim2sim_scene_20261016", "docs/agilekickball_v4/sim2sim_20261014/README.md", "projects/football/README.md", "projects/README.md", "README.md", "agent/plan/agilekickball-s2s-scene-depth-20261016.md", "agent/task/agilekickball-s2s-scene-depth-20261016.md", "agent/report/agilekickball-s2s-scene-depth-20261016.md", "agent/handoff/agilekickball-s2s-scene-depth-20261016.md", "tests/test_kickball_ball_speed.py"]
---

# MuJoCo场景深度

默认s2s改为完整可见场景光轴深度，机身、地面、球和场景物体参与最近求交。复用v5相机profile和部署预处理，保留显式legacy解析重放。v4权重用于分布变化诊断；v5契约严格匹配。验证遮挡、光轴/单位、相机姿态、历史时序、旧接口与无窗口闭环，不启动训练或真实硬件。
