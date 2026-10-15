---
task_id: "carrybox-amp-default-20261014"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
development_modes: ["ML_DATA_PIPELINE"]
original_request: "把搬箱子任务改成用新的amp数据集合"
allowed_paths: ["projects/findbox/README.md", "projects/README.md", "docs/carrybox/amp_default_20261014", "agent/plan/carrybox-amp-default-20261014.md", "agent/task/carrybox-amp-default-20261014.md", "agent/report/carrybox-amp-default-20261014.md", "agent/handoff/carrybox-amp-default-20261014.md"]
forbidden_scope: ["改动足球、动作张量或无特权观测边界", "启动、停止、重启正式训练或热更换缓存", "绕过checkpoint数据身份校验"]
steps: ["核对AMP/PPO配置和walled参考初始化的新默认目录", "复跑现有CPU加载、AMP更新/恢复与RSI初始化检查", "只读核对当前正式进程与checkpoint数据身份", "记录新默认生效范围和旧进程限制"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox_amp.py -v"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox_walled.py -v"}]
stop_conditions: ["新数据hash或AMP/RSI默认不一致", "需要修改算法或训练运行状态"]
safeguards: ["保留全部既有未提交改动和历史数据", "15段/4155帧、抱箱300帧5秒、AMP组40/40/20保持", "AMP纯本体，actor/critic不引入箱子真值", "明确新进程默认与旧进程缓存不是同一状态"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

当前默认路径已由前次目录迁移设置为assets/motions/findbox。执行最小验收及记录，避免为已有行为添加冗余代码。用户本次未明确要求重启长训，当前旧进程不做热切换。
