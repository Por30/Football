---
task_id: "carrybox-wall4-convergence"
language: "zh-CN"
axes: ["E", "L", "A"]
risk_tier: "T2"
artifact: "PLAN"
status: "DONE"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "tests/test_carrybox_convergence.py", "scripts/analyze_carrybox_training.py", "scripts/rsl_rl/audit_carrybox_convergence.py", "scripts/rsl_rl/audit_carrybox_convergence.sh", "docs/carrybox/convergence_20261014", "docs/carrybox/walled/README.md", "projects", "README.md", "agent", "logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013"]
---

停止原正式训练及队列，保留数据与模型。以正式曲线、即时/历史终止反例和真实仿真回放核实早死及AMP归零链条；仅修正已经证实的实现错误，不在本轮重新开展正式训练或宣称收敛。原X2父奖励/热启动流程缺少源码，只能按用户说明列明已知差异。

执行完成：已停止进程，明确历史term奖励泄漏并修复，21CPU及16环境回放通过；动作范围问题已量化，完整设计已说明。保持停止，没有新的收敛宣称。
