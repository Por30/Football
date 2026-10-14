---
task_id: "carrybox-wall4-runtime-fix"
language: "zh-CN"
axes: ["E", "L", "A"]
risk_tier: "T2"
artifact: "PLAN"
status: "DONE"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "scripts/rsl_rl/diagnose_carrybox_walled.py", "scripts/rsl_rl/diagnose_carrybox_walled.sh", "scripts/rsl_rl/smoke_carrybox_walled.py", "scripts/rsl_rl/smoke_carrybox_walled.sh", "scripts/rsl_rl/validate_carrybox_runtime.sh", "scripts/rsl_rl/queue_wall4.py", "scripts/rsl_rl/train_carrybox_walled.sh", "tests/test_carrybox_queue.py", "tests/test_carrybox_walled.py", "docs/carrybox/wall4_repair", "docs/carrybox/walled/README.md", "projects", "README.md", "agent", "logs/rsl_rl/g1_carrybox_depth"]
---

新授权继续修复wall4 GPU训练故障。先做可控诊断建立根因证据，再改最小必要路径；验收不限首次迭代，必须持续跨更新/保存/重置，并保留场景遮挡与纯感知策略输入。正式训练沿用用户已授权的football完成后串行安排。唯一只读专家已核对PhysX张量frontend的连续类型转换，未发现重复索引，不据此改系统库。

执行结果：修复后19项CPU、两变体4环境20＋2轮及wall4 128环境50＋2轮通过。新等待器2300674已READY/WAITING_FOOTBALL；正式训练尚未启动，遵守football完成后串行顺序。详见同名Report/Handoff及docs/carrybox/wall4_repair。
