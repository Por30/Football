---
task_id: "carrybox-wall4-after-football"
language: "zh-CN"
axes: ["E", "L", "A"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "scripts/rsl_rl/smoke_carrybox_walled.py", "scripts/rsl_rl/smoke_carrybox_walled.sh", "scripts/rsl_rl/queue_wall4.py", "tests/test_carrybox_queue.py", "docs/carrybox/wall4_queue", "projects", "README.md", "agent", "logs/rsl_rl/g1_carrybox_depth"]
---

用户已授权等待当前足球正式训练完成后启动wall4。先修复运动学刚体速度API违规，验证实际runner跨PPO更新、保存及reset，再以持久后台串行启动器等待足球最终49999 checkpoint完整性。正式训练采用wall4默认128环境、40000轮、seed42，从头训练。足球运行中只做4环境有界短测；128环境预检在足球完成后执行。只读组合轴专家确认API违规，未证明其为CUDA700唯一根因。不得将静态遮挡审计当作动态训练就绪。
