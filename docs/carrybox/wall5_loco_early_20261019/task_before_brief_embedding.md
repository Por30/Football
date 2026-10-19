---
task_id: "carrybox-wall5-loco-early-20261019"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "用户反馈没抱箱时一开始就reset、尚未学会移动；排查行走起点前20步失败原因"
development_modes: ["SYSTEM_TUNING", "MODEL_DEPLOYMENT"]
allowed_paths: ["docs/carrybox/wall5_loco_early_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-loco-early-20261019.md", "agent/task/carrybox-wall5-loco-early-20261019.md", "agent/report/carrybox-wall5-loco-early-20261019.md", "agent/handoff/carrybox-wall5-loco-early-20261019.md"]
forbidden_scope: ["修改生产环境/奖励/RSI/AMP/网络/数据", "停止重启或启动正式训练", "把参考轨迹或持箱RSI存活称作已学会地面拾箱"]
steps: ["核对当前运行状态、model11200和参考初始化/动作/奖励路径", "同种子同初态16环境100步对照策略均值/保持参考q/默认q/参考轨迹/保持参考q清初速，记录首终止及前20步", "核对完整训练日志分技能采样占比/奖励尺度与动作夹限", "按证据归因并记录已知局限及后续最小修复方向"]
tests: [{"command": "bash docs/carrybox/wall5_loco_early_20261019/check.sh"}, {"command": "bash docs/carrybox/wall5_loco_early_20261019/replay.sh"}]
stop_conditions: ["每个失败检查最多两次范围内修复", "少于4GiB可用显存不启动诊断", "checkpoint或归档环境契约不匹配则停止"]
safeguards: ["仅诊断子进程，用真实rev14 model11200严格加载；当前正式训练进程已不存在，不推断退出原因", "保持物理/噪声/原推扰与终止；仅诊断集中loco初始化，reset概率生产80/0/20不改", "以每个环境首次失败为统计单位，完成/100步存活分开；记录实际push时机，首20步不归因于尚未施加的push", "控制组通过同一动作处理链映射目标，保留真实clip与物理限位并记录；初速清零为显式独立条件"]
expert_required: true
expert_brief: null
device_actions: []
real_device_authorized: false
---

先定位启动即倒的环节，不先改RSI、奖励或放宽终止。只读组合专家brief待补，命令与范围冻结。
