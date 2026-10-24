---
task_id: "carrybox-wall10-play4-20261024-1130"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["docs/carrybox/wall10_play4_20261024_1130", "outputs/carrybox/wall10_play4_20261024_1130", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall10-play4-20261024-1130.md", "agent/task/carrybox-wall10-play4-20261024-1130.md", "agent/report/carrybox-wall10-play4-20261024-1130.md", "agent/handoff/carrybox-wall10-play4-20261024-1130.md"]
original_request: "录下最新ckp play效果"
development_modes: ["MODEL_DEPLOYMENT"]
forbidden_scope: ["修改生产任务/模型/数据", "停止或重启正式训练", "挑选成功片段或将参考持箱计为地面拾箱"]
steps: ["锁定最新完整checkpoint和真实进程资源", "复用已验证脚本录制4环境20秒回放", "完整解码并核对关键帧、接触与抬升记录", "交付视频并更新项目及工程记录"]
tests: [{"command": "bash docs/carrybox/wall10_play4_20261024_1130/record_and_check.sh"}]
stop_conditions: ["契约/权重/源码不一致", "GPU空闲显存不足6GiB", "两次范围内修复后检查仍失败"]
safeguards: ["4环境seed42均值动作，保留随机reset、噪声和物理扰动", "旧输出不覆盖，全部失败保留，渲染不推进物理", "正式训练持续；单seed录像不代表总体成功率"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

锁定model_10000；保持上次20mm高位镜头、直射照明、1080p/25fps和深度角标。
