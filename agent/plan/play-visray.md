---
task_id: "ENG-PLAY-VISRAY-20260922"
language: "zh-CN"
axes: ["P"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["scripts/rsl_rl/play.py", "scripts/rsl_rl/cli_args.py", "scripts/rsl_rl/depth_ray_visualizer.py", "scripts/rsl_rl/smoke_play_visray.py", "scripts/rsl_rl/smoke_play_visray.sh", "tests/test_play_visray.py", "docs/play_visray", "agent"]
---

play新增--visray，默认关闭，仅播放使用debug_draw绿色稀疏射线/像素端点；复用已实例化synthetic_ball_depth_image的ray_x/y/z、安装位姿与最新perception历史帧，不重新调用观测或消耗随机数，不创建碰撞物体。覆盖用户v0命令，v1共享观测也支持；延迟深度子类明确拒绝，避免把历史帧投到当前位姿。显示全部请求播放环境，无训练改动。
