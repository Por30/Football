---
task_id: "carrybox-wall5-play4-rev28-20261023"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
allowed_paths: ["docs/carrybox/wall5_play4_rev28_20261023", "outputs/carrybox/wall5_play4_rev28_20261023", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-play4-rev28-20261023.md", "agent/task/carrybox-wall5-play4-rev28-20261023.md", "agent/report/carrybox-wall5-play4-rev28-20261023.md", "agent/handoff/carrybox-wall5-play4-rev28-20261023.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "那你就录制下最新的ckp"
development_modes: ["MODEL_DEPLOYMENT"]
forbidden_scope: ["不修改生产任务/数据/模型或训练进程", "不筛掉失败，不把参考持箱当地面拾起"]
steps: ["锁定最新完整checkpoint、源码与训练进程身份", "复用四相机录像脚本，严格加载rev28干净深度配置", "录制20秒，完整解码并检查关键帧/回合", "保存行为摘要、报告和项目入口"]
tests: [{"command": "bash docs/carrybox/wall5_play4_rev28_20261023/record_and_check.sh"}]
stop_conditions: ["源码/模型/契约不符即停", "显存不足6GiB不运行", "最多两次范围内修复，保留失败记录"]
safeguards: ["4环境seed42均值动作，实际rev28课程/reset，真实遮挡保持", "严格加载，权重和生产源码不变，旁观渲染不推进物理", "正式训练保持，既有输出不覆盖；单seed四环境不能推出总体成功率"]
expert_required: false
device_actions: []
real_device_authorized: false
---

锁定rev28正式训练最新完整model_1200.pt，4环境seed42均值动作，高位四相机20秒，按模型迭代恢复本版本yaw/推扰课程。完整保存失败及reset，核对原始深度/配置/权重和视频解码。只生成录像与工程记录，正式训练继续。
