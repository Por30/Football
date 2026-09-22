---
task_id: "ENG-PLAY-VISRAY-20260922"
language: "zh-CN"
axes: ["P"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["SIMULATOR_EXTENSION"]
original_request: "play增加可开关--visray，用绿色射线点可视化深度获取FOV"
allowed_paths: ["scripts/rsl_rl/play.py", "scripts/rsl_rl/cli_args.py", "scripts/rsl_rl/depth_ray_visualizer.py", "scripts/rsl_rl/smoke_play_visray.py", "scripts/rsl_rl/smoke_play_visray.sh", "tests/test_play_visray.py", "docs/play_visray", "agent"]
forbidden_scope: ["改策略/观测/课程/奖励/物理配置", "长训练/用户进程/真实设备"]
steps: ["添加仅play使用的可选参数", "实现同传感器几何的debug draw并接入播放循环", "验证坐标系/深度距离/最新帧/生命周期及实际渲染", "文档和回执校验"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_play_visray.py"}, {"command": "bash scripts/rsl_rl/smoke_play_visray.sh"}]
stop_conditions: ["修改超出显示范围", "同一问题修复超过两次"]
safeguards: ["默认关闭不加载debug draw；不重新计算观测、不消耗RNG、不改任何训练状态", "复用ROS相机ray单位方向、torso世界位姿及offset quaternion；深度是沿射线欧氏距离", "只读最后历史帧；维度异常或不支持的感知项明确报错", "绿色是解析球深度/FOV，远端不等于真实场景点云；不是RTX或地面/机身遮挡射线", "稀疏线包含边界；每帧清除旧图元，退出清理", "真实渲染smoke验证debug draw图元计数和截图；不把CPU边界替身称为GUI人工验证"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

play新增--visray，默认关闭，仅播放使用debug_draw绿色稀疏射线/像素端点；复用已实例化synthetic_ball_depth_image的ray_x/y/z、安装位姿与最新perception历史帧，不重新调用观测或消耗随机数，不创建碰撞物体。覆盖用户v0命令，v1共享观测也支持；延迟深度子类明确拒绝，避免把历史帧投到当前位姿。显示全部请求播放环境，无训练改动。
