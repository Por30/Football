---
task_id: "carrybox-wall5-semantic-20261020"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "DONE"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_reward_geometry.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "source/perceptual_ball/perceptual_ball/carrybox_walled.py", "tests/test_carrybox_reward_geometry.py", "tests/test_carrybox_reset_bug.py", "tests/test_carrybox_distance3d.py", "docs/carrybox/wall5_semantic_20261020", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-semantic-20261020.md", "agent/task/carrybox-wall5-semantic-20261020.md", "agent/report/carrybox-wall5-semantic-20261020.md", "agent/handoff/carrybox-wall5-semantic-20261020.md"]
---

用户已选择仅做G1奖励/阈值语义适配并正式重启。先以当前资产与参考数据的PhysX几何读回确定身高、手箱和足箱关系；集中配置距离/高度阈值，仅wall5启用。去除过强stability奖励及walk乘法，保留一次性失败罚、RSI/推扰课程和网络/AMP；standup和search改为pelvis参考。roll/pitch保持，低高度终止随体型核定。短测通过后停止旧rev18，4096 fresh启动rev19并验收。

实现、短测和用户授权的正式启动验收完成；40000轮训练仍在后台进行。具体数值与时间快照见同任务Report/Handoff。
