---
task_id: "AGILE-V2-LAUNCH-20260925"
language: "zh-CN"
axes: ["A"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["logs", "docs/agilekickball_v2/launch_20260925", "agent/plan/agilekickball-v2-launch-20260925.md", "agent/task/agilekickball-v2-launch-20260925.md", "agent/report/agilekickball-v2-launch-20260925.md", "agent/handoff/agilekickball-v2-launch-20260925.md"]
development_modes: ["MODEL_DEPLOYMENT"]
original_request: "排查完原因之后直接从头开始v2的训练，你在后台帮我启动"
forbidden_scope: ["修改训练源码或课程", "resume旧checkpoint", "重复启动训练或中止其他用户进程"]
steps: ["确认版本GPU与重复进程", "脱离会话从零启动4096环境50000轮", "验证首轮更新事件和schema5", "记录PID日志目录和回执"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/agilekickball_v2/launch_20260925/verify_start.py"}]
stop_conditions: ["启动退出或CUDA OOM", "存在其他训练进程", "验证失败两次"]
safeguards: ["用户本轮明确授权长训练，优先于上一轮不启动边界", "不resume，固定seed42 cuda:0 4096环境50000轮", "新run与日志独立，进程脱离终端", "用实际事件和checkpoint核验新版及学习迭代"]
expert_required: false
device_actions: []
real_device_authorized: false
---

用户明确要求后台启动已验证v2。只执行从零训练并验证启动成功；不再改任务，不resume。
