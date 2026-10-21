---
task_id: "carrybox-wall5-play4-high-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "再录一下最新的ckp 摄像头拉高一点 一次录4个机器人"
development_modes: ["MODEL_DEPLOYMENT"]
allowed_paths: ["docs/carrybox/wall5_play4_high_20261021", "outputs/carrybox/wall5_play4_high_20261021", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-play4-high-20261021.md", "agent/task/carrybox-wall5-play4-high-20261021.md", "agent/report/carrybox-wall5-play4-high-20261021.md", "agent/handoff/carrybox-wall5-play4-high-20261021.md"]
forbidden_scope: ["不修改生产任务、数据、checkpoint或学习配置", "不停止或重启后台训练", "不筛除失败回合或将hold参考起点算成拾箱成功"]
steps: ["锁定最新完整checkpoint及正式进程/源码身份", "复用回放路径，四环境同步控制，四台较高旁观相机合成20秒四宫格", "严格加载并实际录制，逐画面完整解码及视觉核对", "保存模型身份、各环境reset/起点标注和项目记录"]
tests: [{"command": "bash docs/carrybox/wall5_play4_high_20261021/record_and_check.sh"}]
stop_conditions: ["契约/源码身份不一致停止，不以weights-only掩盖差异", "可用显存不足6GiB不启动录制", "失败检查最多范围内修复两次，保留失败工件"]
safeguards: ["仅独立play，不改后台PID570043及生产源文件/模型", "按checkpoint迭代恢复本run课程锚点0，保持深度噪声/物理/终止/RSI", "4环境保持默认midpoint配额[0,0,0,2]，持箱参考起点必须标注，不能当成地面拾箱成功", "四台旁观相机约5.8m高，四幅图来自同一物理时刻，渲染不推进物理；相机不进入actor", "50Hz控制/25fps、20秒500帧、1920x1080、四格均完整解码并检查可见性", "录制前可用显存至少6GiB；不覆盖历史视频，失败工件保留"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

复用已验证的四相机录制工具：4环境同一步物理状态，分别使用升高旁观相机并合成同步四宫格。每格可见机器人和箱子，保留深度角标、reset与初始技能；单段回放不作为成功率评估。生产任务、模型和后台训练保持。
