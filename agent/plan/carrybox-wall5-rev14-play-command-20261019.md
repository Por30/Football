---
task_id: "carrybox-wall5-rev14-play-command-20261019"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "PLAN"
status: "READY"
---

新增独立历史播放命令，避免当前revision15与指定revision14 checkpoint契约冲突；复用上一轮实际录制已验证的归档配置与网络，不重新启动GPU验证。
