---
task_id: "agilekickball-depth-live"
language: "zh-CN"
axes: ["P"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "我启动s2s的时候同步出现一个窗口 显示图图图"
allowed_paths: ["scripts/sim2sim", "docs/agilekickball_v4/sim2sim_20261014", "projects/football/README.md", "projects/README.md", "agent"]
forbidden_scope: ["改变策略/物理/训练", "真机控制", "修改历史验证产物"]
development_modes: ["ML_DATA_PIPELINE"]
steps: ["增加独立深度窗口", "图形启动默认启用并管理关闭", "运行原有检查和双窗口短测", "更新使用命令及记录"]
tests: [{"command": "/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_mujoco.py -v"}, {"command": "env LIBGL_ALWAYS_SOFTWARE=1 /home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --duration 2 --physics-dt 0.005 --output docs/agilekickball_v4/sim2sim_20261014/depth_live_smoke.json"}]
stop_conditions: ["图形初始化失败且两次局部修复无效"]
safeguards: ["直接读取现有depth，不重复observe", "headless不创建窗口；单独关闭深度窗口不停止物理仿真", "窗口退出时回收，保留米制固定色标与v4语义"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

T1局部显示出口，主Agent直接实现。使用已有Tk/Pillow/colormap，无新依赖；真实桌面短测2秒。
