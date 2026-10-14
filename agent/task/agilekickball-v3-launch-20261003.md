---
task_id: "AGILE-V3-LAUNCH-20261003"
language: "zh-CN"
axes: ["A"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
development_modes: ["MODEL_DEPLOYMENT"]
original_request: "重新构建完成v3任务之后  你直接在后台启动式式的训练吧"
allowed_paths: ["logs", "docs/agilekickball_v3/launch_20261003", "agent/plan/agilekickball-v3-launch-20261003.md", "agent/task/agilekickball-v3-launch-20261003.md", "agent/report/agilekickball-v3-launch-20261003.md", "agent/handoff/agilekickball-v3-launch-20261003.md"]
forbidden_scope: ["改变已验证训练源码或配置", "resume 旧 checkpoint", "重复启动训练或中止其他进程"]
steps: ["核对 v3 交接与 GPU/已有进程", "独立会话启动正式从零训练并记录 PID", "验证真实配置、至少三次迭代及 checkpoint", "保存运行路径和回执并交接"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/agilekickball_v3/launch_20261003/verify_start.py"}]
stop_conditions: ["已有训练进程", "启动退出或 CUDA OOM", "两次范围内修复后仍不能验证启动"]
safeguards: ["用户本轮明确授权后台长训，取代前轮仅短测边界", "4096 环境、cuda:0、50000 迭代、seed42，不 resume", "stdin 脱离终端、独立 session、独立日志文件，保存 PID 与启动 tick", "依据实际日志、配置、有限 checkpoint 权重与辅助优化器确认成功"]
expert_required: false
device_actions: []
real_device_authorized: false
---

本次仅启动已经完成重建和验证的 v3 contact_outcome_20261003。复用现有正式脚本，不重新构建另一版本。启动验收之后保持训练运行；无需等待 50000 迭代完成。
