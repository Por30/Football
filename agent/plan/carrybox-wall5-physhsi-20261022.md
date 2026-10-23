---
task_id: "carrybox-wall5-physhsi-20261022"
language: "zh-CN"
axes: ["E", "C", "L"]
risk_tier: "T2"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_physhsi.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_physhsi.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "tests/test_carrybox_physhsi.py", "docs/carrybox/wall5_physhsi_20261022", "projects/README.md", "projects/findbox/README.md", "logs/rsl_rl/g1_carrybox_depth/walled5", "agent/plan/carrybox-wall5-physhsi-20261022.md", "agent/task/carrybox-wall5-physhsi-20261022.md", "agent/report/carrybox-wall5-physhsi-20261022.md", "agent/handoff/carrybox-wall5-physhsi-20261022.md"]
artifact: "PLAN"
---

按用户要求迁移wall5碰撞与reset到本地PhysHSI G1语义，通过CPU和仿真PPO/AMP更新、恢复/导出验证后停止当前wall5并从零启动4096正式训练。只作用wall5；保留深度actor/critic123/AMP及任务奖励核心，禁碰其他任务或共享USD。机器人原URDF碰撞+肩胶囊，自碰撞启用且取消髋膝通用碰撞扣分；每次混合20%默认/80%参考，参考技能权重8/2/2；根速度覆盖、关节扰动及物理步动作延迟，匹配PhysHSI普通carrybox终止。完整pickup RSI与支撑平台按用户范围澄清或已声明默认实施，普通FindBox箱位分布不默认扩展为放置任务。短测通过仅代表运行有效，不能宣称收敛。
