---
task_id: "carrybox-wall5-rev14-play-command-20261019"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "给出指定wall5 rev14 model11200的play命令，保持原环境可播放"
development_modes: ["MODEL_DEPLOYMENT"]
allowed_paths: ["docs/carrybox/wall5_rev14_play_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-rev14-play-command-20261019.md", "agent/task/carrybox-wall5-rev14-play-command-20261019.md", "agent/report/carrybox-wall5-rev14-play-command-20261019.md", "agent/handoff/carrybox-wall5-rev14-play-command-20261019.md"]
forbidden_scope: ["改动生产任务或共享play", "启动停止重启正式训练", "把rev15 weights-only播放称作rev14历史环境"]
steps: ["核对模型与已验收的rev14归档来源", "建立独立GUI播放入口，严格契约和全部权重加载，复用录像路径", "CPU检查语法/权重/归档hash并记录命令，不自动启动GUI或GPU仿真"]
tests: [{"command": "bash docs/carrybox/wall5_rev14_play_20261019/check.sh"}]
stop_conditions: ["模型或归档身份不匹配停止", "每个失败检查最多范围内修复两次"]
safeguards: ["原噪声/RSI/推扰/摩擦保持，课程按fresh本run零锚点重建", "只读checkpoint，actor均值推理，不创建optimizer或训练/导出文件", "明确本次仅CPU验证，GUI物理回放路径复用此前已通过20秒录像"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

新增独立历史播放命令，避免当前revision15与指定revision14 checkpoint契约冲突；复用上一轮实际录制已验证的归档配置与网络，不重新启动GPU验证。
