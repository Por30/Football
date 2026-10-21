---
task_id: "carrybox-wall5-rsi5-fresh-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["docs/carrybox/wall5_rsi5_fresh_20261021", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-rsi5-fresh-20261021.md", "agent/task/carrybox-wall5-rsi5-fresh-20261021.md", "agent/report/carrybox-wall5-rsi5-fresh-20261021.md", "agent/handoff/carrybox-wall5-rsi5-fresh-20261021.md"]
original_request: "你停掉当前训后后后 重新动动新的训练"
development_modes: ["ML_TRAINING"]
forbidden_scope: ["不修改生产代码、数据或其他训练配方", "不恢复旧权重/优化器", "不操作其他项目进程或删除历史模型/日志"]
steps: ["核对旧PID身份、已通过新RSI验收、源码和数据身份", "停止身份匹配的旧训练并保留退出及checkpoint记录", "独立新run从零启动wall5 4096环境/seed42/40000轮", "核验持续更新、新比例/首模型/耗时并更新项目记录"]
tests: [{"command": "bash docs/carrybox/wall5_rsi5_fresh_20261021/start_and_verify.sh"}]
stop_conditions: ["旧进程身份不符或源码hash变化则停止", "旧进程未退出或可用显存小于19000MiB不启动", "启动报错/非有限或新契约不符停止验收", "检查失败最多两次范围内修复，不重复启动"]
safeguards: ["启动前按命令与start_ticks核对旧PID；只对该PID发信号", "旧checkpoint/日志保留，明确未保存尾部不可恢复", "launch.json防重复启动，日志新建不覆盖", "无resume/checkpoint/warm_start参数；真实新模型验证优化器step20和AMP count61440", "启动后至少观察16个完整迭代，热身后10轮最长<=6秒；不等同收敛", "单L轴T2，无需多轴专家；无实机动作"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

按用户要求停止当前wall5 PID570043，并以新RSI75/5/20从头启动4096环境正式训练。保持revision19奖励/深度/AMP/PPO等其余配置；旧模型和日志保留。复用已通过的20环境reset验收，本次验收真实正式进程前16轮、首模型契约、全新优化器/归一化状态及6秒性能目标。
