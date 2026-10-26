---
task_id: "agilekickball-v4-demo-20261026"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "PLAN"
status: "READY"
---

按用户指定v4 model_49999播放并录制30秒1080p/25fps单机器人demo。复用正式play的runner、严格加载与课程恢复，保留默认seed42与全部reset；仅调整旁观相机、输出和渲染资源。原checkpoint及正在运行的v11训练保留。验收完整解码、帧数/时长、有限推理和关键画面。
