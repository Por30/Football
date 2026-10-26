---
task_id: "agilekickball-v4-demo-20261026"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
development_modes: ["MODEL_DEPLOYMENT"]
original_request: "录一段/home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v4/2026-10-12_13-48-41_return_to_sender_20261012_v3init/model_49999.pt play的效果为mp4 我要用作demo展示"
allowed_paths: ["docs/agilekickball_v4/demo_20261026", "outputs/football/agilekickball_v4_demo_20261026", "projects/README.md", "projects/football/README.md", "agent/plan/agilekickball-v4-demo-20261026.md", "agent/task/agilekickball-v4-demo-20261026.md", "agent/report/agilekickball-v4-demo-20261026.md", "agent/handoff/agilekickball-v4-demo-20261026.md"]
forbidden_scope: ["修改生产代码、训练配置、数据或checkpoint", "停止、重启或改变已有训练", "未标明的速度覆盖、时间变速或隐藏失败"]
steps: ["只读核对模型、原任务和GPU/进程", "使用原v4推理和课程录制30秒单机器人", "完整解码并检查画面、有限值与模型身份", "交付MP4并更新项目和工程记录"]
tests: [{"command": "bash docs/agilekickball_v4/demo_20261026/record_and_check.sh"}]
stop_conditions: ["模型/课程契约不匹配", "启动时GPU可用显存少于6GiB", "两次范围内修复后仍失败"]
safeguards: ["保留全部30秒和重置，不以录像代替总体成功率", "模型严格加载，录制前后hash及权重不变", "有限观测/动作，额外渲染不推进物理", "1环境seed42、均值动作；原课程球速与目标门"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

本次任务替代之前的训练启动跟进，范围仅为用户指定旧v4模型的demo录制。默认完整连续30秒，不筛选seed或成功片段。
