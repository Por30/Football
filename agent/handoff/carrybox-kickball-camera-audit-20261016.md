---
task_id: "carrybox-kickball-camera-audit-20261016"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T0"
artifact: "HANDOFF"
status: "NO_CODE_CHANGE"
changed_files: ["docs/carrybox/camera_crosscheck_20261016/README.md", "docs/carrybox/camera_crosscheck_20261016/evidence.json", "docs/carrybox/camera_crosscheck_20261016/receipts.json", "docs/carrybox/camera_crosscheck_20261016/artifact_validation.json", "projects/README.md", "projects/findbox/README.md", "projects/football/README.md", "agent/plan/carrybox-kickball-camera-audit-20261016.md", "agent/task/carrybox-kickball-camera-audit-20261016.md", "agent/report/carrybox-kickball-camera-audit-20261016.md", "agent/handoff/carrybox-kickball-camera-audit-20261016.md"]
task_contract_sha256: "c55dd4d34f0cbfbca9475cd937d2f97c7ce249b1563bc4ccebe295d4124c5bca"
tests: []
resume_command: null
---

核查完成，生产代码及进程未修改。安装位姿匹配官方G1 rev_1_0；Kickball v4/v5训练和CarryBox wall3–5仍使用58°垂直FOV，和官方图示55.2°不同。足球MuJoCo官方参考profile仅为无深度契约模型的默认，v5导出优先使用模型自身profile。v4无场景遮挡，v5/Warp wall包含现有任务几何；新增障碍仍须注册射线目标。

相机参数、频率、深度语义、归一化及历史长度对照和19个文件hash见docs/carrybox/camera_crosscheck_20261016/README.md及evidence.json。wall相机扰动精确为随机方向的固定1cm位移。实机K/光心/单位/流配置尚未获得；本次未声称修复或实机验收。

T0配置审计，无冻结测试；工程runner保存空测试列表，未启动仿真/GPU/真实硬件。整理证据时系统Python不支持zoneinfo，改用标准库固定JST时区后成功保存，不涉及生产代码。已检查本次文档内本地链接及工件交叉一致性。

后续若调整相机，使用真实深度流K和相同crop/resize；分别对齐训练/部署采集时序，保留足球米制8帧与搬箱子除以3/4帧输入，补齐CarryBox相机契约并版本化。当前正式训练保持原配置，勿将此审计解释为已切换。
