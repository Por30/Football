---
task_id: "agilekickball-official-camera-20261016"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "DONE"
allowed_paths: ["docs/agilekickball_v5/official_g1_camera_20261016", "docs/agilekickball_v5/camera_unitree_g1_d435i.json", "docs/agilekickball_v5/sim2sim_scene_20261016/README.md", "scripts/sim2sim/scene_depth.py", "scripts/sim2sim/kickball_mujoco.py", "source/perceptual_ball/perceptual_ball/kickball_depth.py", "tests/test_kickball_scene_depth.py", "README.md", "projects/football/README.md", "projects/README.md", "agent/plan/agilekickball-official-camera-20261016.md", "agent/task/agilekickball-official-camera-20261016.md", "agent/report/agilekickball-official-camera-20261016.md", "agent/handoff/agilekickball-official-camera-20261016.md"]
---

# 官方G1相机对齐

根据官方Depth Camera Routine，D435i示例为640x480 Z16 60fps；安装从官方rev_1_0 URDF核对。保持控制和动力学步长，新增物理tick绝对相位采集，明确离散仿真时间量化与未实测内参。
