---
task_id: "carrybox-wall4-restart-20261014"
language: "zh-CN"
axes: ["A"]
risk_tier: "T1"
artifact: "PLAN"
status: "DONE"
allowed_paths: ["agent", "docs/carrybox/restart_20261014", "projects/README.md", "projects/findbox/README.md", "README.md", "logs/rsl_rl/g1_carrybox_depth/walled4"]
---

按用户最新指令重新启动修正跌倒奖励的wall4，从头初始化而不恢复退化模型。保持128环境、seed42、40000轮及根findbox数据；不在本轮改变控制范围/PD。验收进程、PPO迭代、checkpoint及AMP早期健康状态；不承诺收敛。

正式启动及早期核查已完成，训练在后台继续。
