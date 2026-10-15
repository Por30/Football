---
task_id: "carrybox-wall-parity-20261015"
language: "zh-CN"
axes: ["E", "L", "C"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "source/perceptual_ball/perceptual_ball/carrybox_walled.py", "tests/test_carrybox_x2.py", "tests/test_carrybox_walled.py", "tests/test_carrybox_wall_parity.py", "docs/carrybox/wall_parity_20261015", "README.md", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall-parity-20261015.md", "agent/task/carrybox-wall-parity-20261015.md", "agent/report/carrybox-wall-parity-20261015.md", "agent/handoff/carrybox-wall-parity-20261015.md", "tests/test_carrybox_queue.py"]
artifact: "TASK"
status: "FROZEN"
original_request: "并把所有修复的改动同步到wall3 保保3 4任务只有障碍物不同 然后给我正式启动wall3任务的训练命令"
development_modes: ["ML_TRAINING", "SIMULATOR_EXTENSION", "CONTROL_LOOP"]
forbidden_scope: ["修改共享G1资产/足球/原始数据", "privileged actor/critic", "停止或启动正式训练", "声称短测证明收敛"]
steps: ["核验差异和冻结范围", "公共头高/限位/动作目标修复", "统一RSI搜索课程训练配方，仅保留场景差异", "CPU与两任务真实仿真更新恢复导出验证", "保存证据与项目说明并提供wall3正式命令"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}]
stop_conditions: ["测试两次范围内修复仍失败", "GPU资源不足或非有限状态", "不进行长期收敛因果推断"]
safeguards: ["保留无特权观测与纯本体AMP", "不改共享资产硬限位、足球及CarryBox-v0", "头部COM跟随旋转并减env origin", "动作目标按真实hard limits裁剪", "场景之外配置严格一致", "正式训练进程保持不动"]
expert_required: true
device_actions: []
real_device_authorized: false
---
CPU-only recheck of the unchanged frozen command after fixing the legacy mock fixture; GPU result is retained separately.
