---
task_id: "carrybox-wall5-play11000-20261019"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "录制指定wall5 revision14 model_11000.pt的play效果为MP4"
development_modes: ["MODEL_DEPLOYMENT"]
allowed_paths: ["docs/carrybox/wall5_play11000_20261019", "outputs/carrybox/wall5_play11000_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-play11000-20261019.md", "agent/task/carrybox-wall5-play11000-20261019.md", "agent/report/carrybox-wall5-play11000-20261019.md", "agent/handoff/carrybox-wall5-play11000-20261019.md"]
forbidden_scope: ["修改生产任务/学习/物理/数据/模型", "停止或重启后台正式训练", "使用rev15环境冒充rev14回放"]
steps: ["核对checkpoint身份/旧配置及GPU资源", "使用归档rev14配置严格加载同模型，均值动作单环境20秒原速录制", "验证500帧/25fps/20秒完整解码并检查画面，保存结果和项目记录"]
tests: [{"command": "bash docs/carrybox/wall5_play11000_20261019/record_and_check.sh"}]
stop_conditions: ["checkpoint契约或模型严格加载不匹配则停止", "显存不足4GiB不启动录制", "每个失败检查最多范围内修复两次"]
safeguards: ["仅独立play进程，正式PID4038923保持；保持原物理/噪声/RSI/终止与障碍", "有效训练迭代11000（yaw12度/推扰满强度），保持自动reset；不筛掉失败镜头", "记录checkpoint/hash、环境契约、动作模式/相机/帧率与完成回合；短视频不作成功率证明"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

默认单环境均值动作播放；先严格核对旧契约，不用当前rev15权重迁移冒充旧环境。测试同时覆盖实际录制及完整解码。
