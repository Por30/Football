---
task_id: "carrybox-wall4-convergence"
language: "zh-CN"
axes: ["E", "L", "A"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "tests/test_carrybox_convergence.py", "scripts/analyze_carrybox_training.py", "scripts/rsl_rl/audit_carrybox_convergence.py", "scripts/rsl_rl/audit_carrybox_convergence.sh", "docs/carrybox/convergence_20261014", "docs/carrybox/walled/README.md", "projects", "README.md", "agent", "logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013"]
original_request: "停止训练 排查一下原因 训练好像没有收敛 我在原先的x2机器人上是能够实现完整的搬起箱子流程的 你排查好问题后 讲一下当前wall4任务是怎么设计的"
forbidden_scope: ["正式训练重启", "足球及共享系统库修改", "删除模型或原始数据"]
development_modes: ["ML_TRAINING", "SIMULATOR_EXTENSION"]
steps: ["停止并归档当前进程状态", "统计曲线并审计奖励/终止/AMP与X2差异", "最小修复确证的wall4实现错误", "离线合同和有界仿真反例验证", "说明当前设计、证据与尚未验证项并同步管理记录"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}, {"command": "/home/cao/ENTER/envs/ball/bin/python scripts/analyze_carrybox_training.py"}, {"command": "bash scripts/rsl_rl/audit_carrybox_convergence.sh"}]
stop_conditions: ["冻结测试失败后最多两次原范围修复", "需要正式长训或实机验证时仅报告后续需求", "没有X2源码时不能宣称逐行复现"]
safeguards: ["正式wall4及等待器保持停止，禁止自动重启", "只读原始数据和原checkpoint，不修改football/系统IsaacLab", "只允许有界诊断回放及测试；无实机操作", "不把短测或辅助损失下降视为拾箱收敛"]
expert_required: true
expert_brief: {"affected_call_path": ["wall4奖励、终止、AMP、RSI、G1控制和正式曲线"], "critical_interfaces": ["即时terminated与历史get_term语义", "10帧AMP有效门控、reward*dt、episode日志归一化"], "invariants": ["actor/critic仅本体深度；football独立"], "smallest_change_locus": ["walled奖励门控及定点诊断"], "mandatory_safeguards": ["正式wall4及等待器保持停止，禁止自动重启", "只读原始数据和原checkpoint，不修改football/系统IsaacLab", "只允许有界诊断回放及测试；无实机操作", "不把短测或辅助损失下降视为拾箱收敛"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "/home/cao/ENTER/envs/ball/bin/python scripts/analyze_carrybox_training.py", "bash scripts/rsl_rl/audit_carrybox_convergence.sh"], "blockers": ["冻结测试失败后最多两次原范围修复", "需要正式长训或实机验证时仅报告后续需求", "没有X2源码时不能宣称逐行复现"]}
device_actions: []
real_device_authorized: false
---

停止原正式训练及队列，保留数据与模型。以正式曲线、即时/历史终止反例和真实仿真回放核实早死及AMP归零链条；仅修正已经证实的实现错误，不在本轮重新开展正式训练或宣称收敛。原X2父奖励/热启动流程缺少源码，只能按用户说明列明已知差异。
