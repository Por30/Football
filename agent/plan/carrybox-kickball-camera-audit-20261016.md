---
task_id: "carrybox-kickball-camera-audit-20261016"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T0"
artifact: "PLAN"
status: "READY"
allowed_paths: ["docs/carrybox/camera_crosscheck_20261016", "projects/README.md", "projects/findbox/README.md", "projects/football/README.md", "agent/plan/carrybox-kickball-camera-audit-20261016.md", "agent/task/carrybox-kickball-camera-audit-20261016.md", "agent/report/carrybox-kickball-camera-audit-20261016.md", "agent/handoff/carrybox-kickball-camera-audit-20261016.md"]
---

核对CarryBox基线/wall3–5与Kickball v4/v5训练、Isaac播放及MuJoCo相机配置，和官方G1 rev_1_0名义安装及视场图对照。仅读取源码、已保存配置和既有验证证据；新增审计记录并更新两项目入口，不修改生产代码、模型或训练进程。

验收：明确各版本实际采用的安装、FOV、频率、深度语义及遮挡范围；区分训练与s2s、名义参数与实机标定；所有结论可回溯到具体文件。
