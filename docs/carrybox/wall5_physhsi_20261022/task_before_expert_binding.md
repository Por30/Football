---
task_id: "carrybox-wall5-physhsi-20261022"
language: "zh-CN"
axes: ["E", "C", "L"]
risk_tier: "T2"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_physhsi.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_physhsi.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "tests/test_carrybox_physhsi.py", "docs/carrybox/wall5_physhsi_20261022", "projects/README.md", "projects/findbox/README.md", "logs/rsl_rl/g1_carrybox_depth/walled5", "agent/plan/carrybox-wall5-physhsi-20261022.md", "agent/task/carrybox-wall5-physhsi-20261022.md", "agent/report/carrybox-wall5-physhsi-20261022.md", "agent/handoff/carrybox-wall5-physhsi-20261022.md"]
artifact: "TASK"
original_request: "把碰撞和逻辑成成phsi版本的然后重动动动训练"
development_modes: ["SIMULATOR_EXTENSION", "CONTROL_LOOP", "ML_TRAINING"]
forbidden_scope: ["不改football/wall3/wall4行为、网络输入或共享USD", "不删历史checkpoint/数据，不操作真实硬件", "不把短测作为收敛证明，不重启未经验证版本"]
steps: ["记录实际训练身份和来源hash，取得组合专家七字段审查", "仅wall5迁移原碰撞与混合RSI、速度/缓存及终止语义", "CPU针对性检查及仿真更新恢复导出；失败原范围最多两次修复", "验证来源一致后停止身份匹配旧run，4096从零启动并核对日志和首模型", "输出差异与范围说明，更新入口和四工件"]
tests: [{"command": "bash docs/carrybox/wall5_physhsi_20261022/cpu.sh"}, {"command": "bash docs/carrybox/wall5_physhsi_20261022/smoke.sh"}, {"command": "bash docs/carrybox/wall5_physhsi_20261022/start_and_verify.sh"}]
stop_conditions: ["来源身份不匹配或非有限/严重物理错误停止启动", "测试失败最多两次原范围修复；不放宽断言或删除测试"]
safeguards: ["参考数据和joint/frame/单位一致；原USD不可改", "延迟以5ms物理步更新，部分reset仅重置对应环境", "checkpoint revision24严格契约，旧版拒绝恢复，新run fresh", "先验证再停止旧任务，保留所有原始证据"]
expert_required: true
expert_brief_path: "docs/carrybox/wall5_physhsi_20261022/expert_brief.json"
device_actions: []
real_device_authorized: false
---

按用户要求迁移wall5碰撞与reset到本地PhysHSI G1语义，通过CPU和仿真PPO/AMP更新、恢复/导出验证后停止当前wall5并从零启动4096正式训练。只作用wall5；保留深度actor/critic123/AMP及任务奖励核心，禁碰其他任务或共享USD。机器人原URDF碰撞+肩胶囊，自碰撞启用且取消髋膝通用碰撞扣分；每次混合20%默认/80%参考，参考技能权重8/2/2；根速度覆盖、关节扰动及物理步动作延迟，匹配PhysHSI普通carrybox终止。完整pickup RSI与支撑平台按用户范围澄清或已声明默认实施，普通FindBox箱位分布不默认扩展为放置任务。短测通过仅代表运行有效，不能宣称收敛。
