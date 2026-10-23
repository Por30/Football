---
task_id: "carrybox-wall5-groundfix-20261022"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "READY"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_physhsi.py", "docs/carrybox/wall5_groundfix_20261022", "projects/README.md", "projects/findbox/README.md", "logs/rsl_rl/g1_carrybox_depth/walled5", "agent/plan/carrybox-wall5-groundfix-20261022.md", "agent/task/carrybox-wall5-groundfix-20261022.md", "agent/report/carrybox-wall5-groundfix-20261022.md", "agent/handoff/carrybox-wall5-groundfix-20261022.md"]
---

恢复PhysHSI的绝对roll>0.5、pitch>1.1终止；修复已确认的当前G1 reset足底穿地，保持采样和控制/奖励配方。复用已有foot hull helper，在最终随机关节角写入并刷新FK后只向上校正到5mm，参考箱子和活动支撑台同步上移。角度阈值变化与接地适配分别记录，不认定为收敛充分条件。通过64环境几何/部分reset/更新恢复短测再停止当前身份匹配进程，从头启动4096正式训练。
