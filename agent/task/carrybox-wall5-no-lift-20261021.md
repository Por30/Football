---
task_id: "carrybox-wall5-no-lift-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["docs/carrybox/wall5_no_lift_20261021", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-no-lift-20261021.md", "agent/task/carrybox-wall5-no-lift-20261021.md", "agent/report/carrybox-wall5-no-lift-20261021.md", "agent/handoff/carrybox-wall5-no-lift-20261021.md"]
original_request: "并且当前没有学会搬起来的的动作"
development_modes: ["MODEL_DEPLOYMENT"]
forbidden_scope: ["不修改生产代码、奖励、数据、checkpoint或启动/停止正式训练", "不把hold参考起点算地面拾箱", "不把一次回放关联当因果证明"]
steps: ["固定日志与checkpoint/源码身份", "读取近250轮训练指标和奖励公式", "20环境均值及采样各1000步，严格原契约回放并统计阶段/接触", "保存结论、局限和项目记录"]
tests: [{"command": "bash docs/carrybox/wall5_no_lift_20261021/check.sh"}]
stop_conditions: ["完整契约不一致停止", "显存不足4096MiB停止回放", "非有限或CUDA错误停止", "最多两次范围内失败修复"]
safeguards: ["使用checkpoint原RSI80/0/20覆盖独立回放cfg；生产默认75/5/20不变", "模型权重/源hash不变、无优化器更新", "均值/采样结果分开，完成/截断回合分开", "保留原深度噪声、推扰及yaw课程"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

只读诊断当前wall5未拾箱：日志近250轮与model回放分开，量化接近/下蹲/手箱接触/离地/奖励分项。保持checkpoint原80/0/20及课程，源码新75/5/20不回退，不操作正式训练。结果用于工程定位，不作为因果实验或总体成功率。
