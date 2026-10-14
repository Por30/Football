---
task_id: "carrybox-findbox-individual-20261014"
language: "zh-CN"
axes: ["S"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
development_modes: ["BUILD_TOOLING"]
original_request: "每一段独立立出来录制 我需要调整数据集"
allowed_paths: ["scripts/visualize_findbox.py", "outputs/carrybox/findbox_individual", "docs/carrybox/dataset_visualization", "projects/findbox/README.md", "projects/README.md", "agent/plan/carrybox-findbox-individual-20261014.md", "agent/task/carrybox-findbox-individual-20261014.md", "agent/report/carrybox-findbox-individual-20261014.md", "agent/handoff/carrybox-findbox-individual-20261014.md"]
forbidden_scope: ["修改原始数据、manifest、训练代码、模型", "覆盖旧视频", "停止、重启或启动训练"]
steps: ["为既有回放工具增加独立片段及单文件选择模式", "按原始60Hz逐帧单独录制17个同名MP4并显示源帧号", "完整解码检查各段帧数、尺寸、源hash及映射", "生成逐段索引并更新项目记录"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python scripts/visualize_findbox.py --verify-only --output outputs/carrybox/findbox_individual"}]
stop_conditions: ["GPU资源不足或运行故障", "关节帧映射不明确", "两次范围内修复后仍验证失败"]
safeguards: ["源数据只读", "保留既有合辑模式", "每个源帧恰好对应一个视频帧", "CPU状态回放、单机器人渲染", "逐段关闭编码器并保存源索引"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

单机器人直接运动学回放，17个独立编码器按片段顺序运行。增加--individual及--clip便于以后指定片段重新生成；全量输出在新目录保留旧录像。现有GPU训练保持运行，仅使用可用资源录制。
