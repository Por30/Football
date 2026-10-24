---
task_id: "carrybox-wall5-rev17-comparison-20261023"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
allowed_paths: ["docs/carrybox/wall5_rev17_comparison_20261023", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-rev17-comparison-20261023.md", "agent/task/carrybox-wall5-rev17-comparison-20261023.md", "agent/report/carrybox-wall5-rev17-comparison-20261023.md", "agent/handoff/carrybox-wall5-rev17-comparison-20261023.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "当前版本和 /home/cao/perceptual_ball/outputs/carrybox/wall5_latest_play_20261020 这个版本有哪些区别"
development_modes: ["ML_TRAINING"]
forbidden_scope: ["不修改生产代码、数据、模型或训练进程", "不将版本差异当成独立因果验证"]
steps: ["确认录像模型和当前正式运行身份", "CPU核对契约、run参数、历史源码并保存差异", "说明关键变化及未改项目，更新工程记录"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_rev17_comparison_20261023/check.py"}]
stop_conditions: ["身份不匹配则停止依赖结论", "核验失败最多两次原范围修复并保留证据"]
safeguards: ["仅CPU读取，不使用GPU", "保留既有修改及所有历史工件"]
expert_required: false
device_actions: []
real_device_authorized: false
---

只读核对用户指定2026-10-20录像的rev17模型与当前正式rev28配方，使用checkpoint契约、真实run参数及hash匹配源码。列出变更、不变项和证据边界；不操作训练。
