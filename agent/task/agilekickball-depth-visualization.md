---
task_id: "agilekickball-depth-visualization"
language: "zh-CN"
axes: ["P"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "可视化一下度度图信息"
allowed_paths: ["scripts/sim2sim/kickball_mujoco.py", "scripts/sim2sim/depth_visualization.py", "docs/agilekickball_v4/sim2sim_20261014", "projects/football/README.md", "projects/README.md", "agent"]
forbidden_scope: ["修改策略输入数值/顺序", "修改PD/模型/发球", "训练或真机", "改写旧验证结果"]
development_modes: ["ML_DATA_PIPELINE"]
steps: ["接只读深度输出", "生成12秒可视化及原始数据", "检查视频帧数/数值并更新记录"]
tests: [{"command": "/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_mujoco.py -v"}, {"command": "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --headless --duration 12 --physics-dt 0.005 --output docs/agilekickball_v4/sim2sim_20261014/depth_visualization/run.json --depth-output docs/agilekickball_v4/sim2sim_20261014/depth_visualization"}]
stop_conditions: ["读取深度时改变策略行为", "视频编码失败经两次修复仍不能输出"]
safeguards: ["只复制实际送入策略的depth；不额外调用observe推进历史", "沿射线米制0.1–3m、far表示无命中，明确v4无场景遮挡", "仅CPU绘图与有限时长仿真，输出存docs"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

使用已有umr的matplotlib/imageio和内置ffmpeg；显示8帧相邻20ms历史、当前最近命中深度和命中像素数，视频10fps。
