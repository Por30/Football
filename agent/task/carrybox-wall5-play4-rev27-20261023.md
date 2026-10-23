---
task_id: "carrybox-wall5-play4-rev27-20261023"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
allowed_paths: ["docs/carrybox/wall5_play4_rev27_20261023", "outputs/carrybox/wall5_play4_rev27_20261023", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-play4-rev27-20261023.md", "agent/task/carrybox-wall5-play4-rev27-20261023.md", "agent/report/carrybox-wall5-play4-rev27-20261023.md", "agent/handoff/carrybox-wall5-play4-rev27-20261023.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "录制一下最新ckp play的效果"
development_modes: ["MODEL_DEPLOYMENT"]
forbidden_scope: ["不改生产任务/数据/模型或训练进程", "不筛掉失败，不把RSI持箱当成地面抓起"]
steps: ["锁定最新完整checkpoint、源码和训练身份", "适配现有四相机录像脚本至rev27固定reset类别", "录制20秒并完整解码、检查关键帧和回合", "生成表现摘要并更新项目记录"]
tests: [{"command": "bash docs/carrybox/wall5_play4_rev27_20261023/record_and_check.sh"}]
stop_conditions: ["源码/模型/契约不符即停", "可用显存不足6GiB不运行", "最多两次范围内修复并保留失败证据"]
safeguards: ["4环境seed42均值动作、原始课程与reset", "严格加载、权重不更新、渲染不推进物理", "正式训练保持运行、既有输出不覆盖"]
expert_required: false
device_actions: []
real_device_authorized: false
---

锁定当前正式rev27训练最新完整model_1400.pt。复用高位四相机录制20秒，保持原reset和课程，完整保存失败回合，检查视频与实际接触/回合统计。只生成录像及记录，正式训练继续。
