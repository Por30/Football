---
task_id: "carrybox-wall5-clean-camera-20261023"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "docs/carrybox/wall5_clean_camera_20261023", "projects/README.md", "projects/findbox/README.md", "logs/rsl_rl/g1_carrybox_depth/walled5", "agent/plan/carrybox-wall5-clean-camera-20261023.md", "agent/task/carrybox-wall5-clean-camera-20261023.md", "agent/report/carrybox-wall5-clean-camera-20261023.md", "agent/handoff/carrybox-wall5-clean-camera-20261023.md"]
artifact: "PLAN"
status: "READY"
---

仅wall5 revision28降低感知/早期外部推扰难度：关闭全部人工深度扰动与安装误差，保留米制、头部相机、ray-cast、自遮挡与障碍遮挡；推扰5000轮warmup＋10000轮ramp。奖励/PD/动作延迟/RSI/碰撞/终止/AMP/网络保持。短测通过后停止身份匹配的旧进程，4096环境seed42从零训练，保留所有历史模型。
