---
task_id: "carrybox-wall5-distance3d-20261020"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "把距离从2d改成3d距离 和x2版本的实现一致"
development_modes: ["ML_TRAINING"]
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "tests/test_carrybox_distance3d.py", "docs/carrybox/wall5_distance3d_20261020", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-distance3d-20261020.md", "agent/task/carrybox-wall5-distance3d-20261020.md", "agent/report/carrybox-wall5-distance3d-20261020.md", "agent/handoff/carrybox-wall5-distance3d-20261020.md"]
forbidden_scope: ["不改变wall3/wall4和足球行为，不改数据/资产/观测/PPO/奖励权重/RSI", "不改变AMP水平封顶、bearing和水平速度方向；不启动、停止或重启正式训练", "不把短测通过宣称为抱箱成功"]
steps: ["核对X2交接中的XYZ任务距离和XY行走方向", "仅wall5启用XYZ距离并统一奖励门控/诊断，升级revision18契约", "执行边界/兼容性CPU检查和4环境更新恢复检查", "记录测试、兼容性及现有正式训练仍为rev17的状态"]
tests: [{"command": "bash docs/carrybox/wall5_distance3d_20261020/check.sh"}, {"command": "bash docs/carrybox/wall5_distance3d_20261020/smoke.sh"}]
stop_conditions: ["NaN/OOM/任务隔离或契约不匹配", "失败只在原范围内修复最多两次，不放宽断言"]
safeguards: ["世界坐标root连杆原点到箱心XYZ欧氏距离，单位米，阈值0.7不变", "水平速度归一化不能误用XYZ距离；保留原严格/非严格边界", "旧契约严格resume拒绝；训练专用输入不得进入actor或导出"]
expert_required: false
device_actions: []
real_device_authorized: false
---

单轴L、T2，主Agent执行。X2原始环境代码在已检索目录未发现，依据用户交接说明，不宣称直接复核X2运行结果。GPU检查限4环境和3轮更新，验证模型仅写本任务docs，正式训练PID254358保持。
