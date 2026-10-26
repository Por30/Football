---
task_id: "carrybox-wall12-start24-20261025"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "你启动wall12的正式训把把"
allowed_paths: ["docs/carrybox/wall12_start24_20261025", "logs/rsl_rl/g1_carrybox_depth/walled12", "projects/README.md", "projects/findbox/README.md", "projects/football/README.md", "agent/plan/carrybox-wall12-start24-20261025.md", "agent/task/carrybox-wall12-start24-20261025.md", "agent/report/carrybox-wall12-start24-20261025.md", "agent/handoff/carrybox-wall12-start24-20261025.md"]
forbidden_scope: ["修改生产代码、训练配方、数据或旧模型", "从docs短测模型初始化正式训练", "未获用户明确授权就停止足球或其他任务", "覆盖已有run或重复启动"]
development_modes: ["ML_TRAINING"]
steps: ["只读核对实际进程、GPU资源、已通过短测与生产源码身份", "准备wall12启动和检查；资源冲突时等用户明确选择，不停止无关训练", "资源释放后独立启动wall12正式fresh run并记录PID和日志", "核验至少12轮、4096×24参数、首checkpoint和辅助头优化器，记录状态"]
tests: [{"command": "bash docs/carrybox/wall12_start24_20261025/check.sh"}]
stop_conditions: ["资源冲突未解决或需停止未授权进程", "生产源码与已验证身份不符且差异未核实", "训练退出、非有限值、CUDA或物理错误", "两次范围内修复后检查仍失败"]
safeguards: ["当前实现是相机系9维位姿回归、12维标签含对称判定尺寸、aux系数1.0；不借启动操作改为X2十二维MSE", "保持4096环境、24步、5×4、seed42、20000轮及墙柱深度噪声", "只新建正式walled12 run，所有已有模型和日志保留", "如用户选择停止足球，先复核PID身份和保存模型，再SIGINT并确认资源释放", "正式启动核验不等于收敛或独立评估"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

T1单学习轴操作，复用wall12既有44项CPU和16环境2＋1轮短测，不再启动额外仿真。

2026-10-25 12:25 JST用户明确追加指令“停止足球 启动wall12”，资源处理授权已具备。按冻结步骤复核足球PID3261150和已保存模型，SIGINT停止后启动wall12；保留此前等待授权的回执，不重复询问。
