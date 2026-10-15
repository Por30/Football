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
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}, {"command": "bash docs/carrybox/wall_parity_20261015/validate.sh"}]
stop_conditions: ["测试两次范围内修复仍失败", "GPU资源不足或非有限状态", "不进行长期收敛因果推断"]
safeguards: ["保留无特权观测与纯本体AMP", "不改共享资产硬限位、足球及CarryBox-v0", "头部COM跟随旋转并减env origin", "动作目标按真实hard limits裁剪", "场景之外配置严格一致", "正式训练进程保持不动", "统计使用实际执行步数，按reset前技能归类"]
expert_required: true
device_actions: []
real_device_authorized: false
expert_brief: {"affected_call_path": ["walled环境reset/step、动作目标、奖励与训练配置；不触及共享PPO/AMP"], "critical_interfaces": ["世界COM高度、实际关节hard limits、无特权观测及revision7恢复契约"], "invariants": ["深度/本体策略与价值输入；15段AMP身份；场景之外wall3/wall4配置相同"], "smallest_change_locus": ["wall专属配置/MDP及共同课程；独立实际步数统计不读取随机timeout年龄"], "mandatory_safeguards": ["保留无特权观测与纯本体AMP", "不改共享资产硬限位、足球及CarryBox-v0", "头部COM跟随旋转并减env origin", "动作目标按真实hard limits裁剪", "场景之外配置严格一致", "正式训练进程保持不动", "统计使用实际执行步数，按reset前技能归类"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "bash docs/carrybox/wall_parity_20261015/validate.sh"], "blockers": []}
---

共同修复wall3/wall4，默认wall3仅墙、wall4墙和3圆柱；仅给正式命令，不启动新训练。修复坐标/限位语义与新训练配方，短测不证明收敛。
范围补充：旧queue单测mock增加新必需的obstacle_cylinder_count=3，保持原碰撞/速度断言不变。
组合专家只读复核发现随机timeout年龄会污染回合统计；已改为实际执行步数并补充CPU回归。冻结测试命令不变。
