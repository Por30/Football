---
task_id: "carrybox-wall5-amp-visualization-20261018"
language: "zh-CN"
axes: ["S"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "可视化当前wall5任务用到的amp数据集"
development_modes: ["BUILD_TOOLING"]
allowed_paths: ["docs/carrybox/wall5_amp_visualization_20261018", "outputs/carrybox/wall5_amp_20261018", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-amp-visualization-20261018.md", "agent/task/carrybox-wall5-amp-visualization-20261018.md", "agent/report/carrybox-wall5-amp-visualization-20261018.md", "agent/handoff/carrybox-wall5-amp-visualization-20261018.md"]
forbidden_scope: ["修改源PT/manifest/训练代码或模型", "停止/重启/调整正在运行的训练", "额外GPU仿真或生成虚构动作"]
steps: ["核对实际正式run配置/模型与13段源hash", "按相同源hash复用既有原生60fps G1逐帧画面，标注新名称并导出完整及分段视频", "逐帧解码/时间索引/源hash与画面对应校验，检查预览", "更新可视化入口及工程记录"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_amp_visualization_20261018/build.py --verify-only"}]
stop_conditions: ["源hash或原生视频帧对应不一致则不复用", "两次范围内修复后检查仍失败则报告阻塞"]
safeguards: ["源数据和既有视频只读，明确画面复用来源", "保留所有3785源帧、60fps和1倍速", "区分AMP采样40/40/20与RSI80/0/20", "标注运动学数据回放；箱体朝向/参考支撑为示意，不作策略成功率证据", "CPU处理、限制编码线程，保持现有训练运行"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

当前正式run使用ground_pickup profile。通过源PT SHA-256将13段映射到已有15段原生60fps录像；更换标题/索引，明确旧画面复用及姿态近似，不修改学习或物理。
