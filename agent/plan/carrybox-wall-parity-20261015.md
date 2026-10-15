---
task_id: "carrybox-wall-parity-20261015"
language: "zh-CN"
axes: ["E", "L", "C"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "source/perceptual_ball/perceptual_ball/carrybox_walled.py", "tests/test_carrybox_x2.py", "tests/test_carrybox_walled.py", "tests/test_carrybox_wall_parity.py", "docs/carrybox/wall_parity_20261015", "README.md", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall-parity-20261015.md", "agent/task/carrybox-wall-parity-20261015.md", "agent/report/carrybox-wall-parity-20261015.md", "agent/handoff/carrybox-wall-parity-20261015.md", "tests/test_carrybox_queue.py"]
artifact: "PLAN"
status: "READY"
---

共同修复wall3/wall4，默认wall3仅墙、wall4墙和3圆柱；仅给正式命令，不启动新训练。修复坐标/限位语义与新训练配方，短测不证明收敛。
范围补充：旧queue单测mock增加新必需的obstacle_cylinder_count=3，保持原碰撞/速度断言不变。
