---
task_id: "agilekickball-ball-speed"
language: "zh-CN"
axes: ["C"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "在做一个接口可以让我手动调整球球的速度"
allowed_paths: ["scripts/sim2sim", "tests/test_kickball_ball_speed.py", "docs/agilekickball_v4/sim2sim_20261014", "projects/football/README.md", "projects/README.md", "agent"]
forbidden_scope: ["改变策略/训练/机器人状态", "真机控制", "覆盖历史验证证据"]
development_modes: ["SIMULATOR_EXTENSION"]
steps: ["添加球速接口与有限正数校验", "添加滑块和立即应用/重新发球，控制边界消费事件", "验证球速度/坐标系/机器人状态不变及真实GUI交互", "更新项目入口与交接记录"]
tests: [{"command": "/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_mujoco.py -v"}, {"command": "env LIBGL_ALWAYS_SOFTWARE=1 /home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_ball_speed.py -v"}]
stop_conditions: ["两次局部修复后仍不能通过指定测试"]
safeguards: ["单位m/s，正且有限；滑块默认0.1至6", "即时调速保留位置与水平运动方向，静止球向-x；滚动角速度转换至球局部坐标", "UI不直接修改MuJoCo；控制步开始处理", "重新发球只重置球；不重置机器人或策略历史", "headless无窗口；关闭深度窗口不中断仿真"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

T1：为现有模拟器球速参数添加交互出口，主Agent直接实现。GUI短测2秒；不启动训练。
