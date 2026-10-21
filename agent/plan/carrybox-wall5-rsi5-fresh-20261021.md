---
task_id: "carrybox-wall5-rsi5-fresh-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "PLAN"
status: "FROZEN"
allowed_paths: ["docs/carrybox/wall5_rsi5_fresh_20261021", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-rsi5-fresh-20261021.md", "agent/task/carrybox-wall5-rsi5-fresh-20261021.md", "agent/report/carrybox-wall5-rsi5-fresh-20261021.md", "agent/handoff/carrybox-wall5-rsi5-fresh-20261021.md"]
---

按用户要求停止当前wall5 PID570043，并以新RSI75/5/20从头启动4096环境正式训练。保持revision19奖励/深度/AMP/PPO等其余配置；旧模型和日志保留。复用已通过的20环境reset验收，本次验收真实正式进程前16轮、首模型契约、全新优化器/归一化状态及6秒性能目标。
