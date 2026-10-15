---
task_id: "carrybox-g1-reset-20261015"
language: "zh-CN"
axes: ["E", "L", "C"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "source/perceptual_ball/perceptual_ball/carrybox_warp_camera.py", "tests/test_carrybox_g1_reset.py", "docs/carrybox/g1_reset_20261015", "logs/rsl_rl/g1_carrybox_depth/walled4", "README.md", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-g1-reset-20261015.md", "agent/task/carrybox-g1-reset-20261015.md", "agent/report/carrybox-g1-reset-20261015.md", "agent/handoff/carrybox-g1-reset-20261015.md", "tests/test_carrybox_walled.py"]
artifact: "PLAN"
status: "READY"
---


先复现并量化站立reset原因，再修复共同实现并后台启动wall4。用户已授权重启，当前实际未发现训练进程；不采用旧失败模型warm-start。正式4096环境，40000轮，seed42；诊断、短测和正式状态分别记录。
范围补充：旧RSI数据加载单测mock补sim.forward/root读回，新增非零补偿后root-box-support同步且其他状态保持的断言；不删除原断言。
