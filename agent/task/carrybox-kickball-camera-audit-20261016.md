---
task_id: "carrybox-kickball-camera-audit-20261016"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T0"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["docs/carrybox/camera_crosscheck_20261016", "projects/README.md", "projects/findbox/README.md", "projects/football/README.md", "agent/plan/carrybox-kickball-camera-audit-20261016.md", "agent/task/carrybox-kickball-camera-audit-20261016.md", "agent/report/carrybox-kickball-camera-audit-20261016.md", "agent/handoff/carrybox-kickball-camera-audit-20261016.md"]
original_request: "同时检查kickball和carrybox两个任务（相机FOV与官方G1安装位置是否一致）"
development_modes: ["MODEL_DEPLOYMENT"]
forbidden_scope: ["改生产相机/策略/训练配置", "启动停止重启训练或GPU仿真", "把名义参数标为实机已标定", "覆盖其他工作区已有修改"]
steps: ["读取两项目入口及实际训练配置", "追踪相机配置、射线、观测和播放部署调用路径", "对照官方安装和FOV并计算各配置的实际FOV", "记录差异、证据及部署边界并更新项目入口"]
tests: []
stop_conditions: ["缺少实机内参或光学外参时明确未验证，不臆造标定"]
safeguards: ["只读生产源码和现有日志", "保留旧checkpoint观测契约", "分开报告训练与播放配置", "文档核查不启动GPU仿真"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

T0只读配置审计，执行源码/JSON/YAML读取和确定性数值换算，无生产代码修改或新增仿真测试。结果记录在docs/carrybox/camera_crosscheck_20261016，并从足球与搬箱子项目入口同时链接。
