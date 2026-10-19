---
task_id: "carrybox-wall5-roll05-start-20261019"
language: "zh-CN"
axes: ["A"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "重新启动正式训练"
development_modes: ["ML_TRAINING"]
allowed_paths: ["docs/carrybox/wall5_roll05_start_20261019", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-roll05-start-20261019.md", "agent/task/carrybox-wall5-roll05-start-20261019.md", "agent/report/carrybox-wall5-roll05-start-20261019.md", "agent/handoff/carrybox-wall5-roll05-start-20261019.md"]
forbidden_scope: ["不改生产源码、PD/默认腿姿/数据/奖励/观察，不恢复已归档候选", "不覆盖旧run或加载旧checkpoint，不干预其他任务", "不以启动成功宣称行走或拾箱收敛"]
steps: ["核对实际进程/GPU/现有roll0.5源码与之前验收", "按用户新指令独立fresh启动4096环境40000轮正式wall5", "核对持续迭代/首checkpoint/有限更新/实际roll契约及分技能日志和耗时", "记录PID命令源码hash并更新项目入口及工程工件"]
tests: [{"command": "bash docs/carrybox/wall5_roll05_start_20261019/verify.sh"}]
stop_conditions: ["资源冲突或身份不匹配则不启动", "若已启动进程退出不重复创建run；先保留异常记录", "有限值/契约不符或启动超时则如实报告，修复仅限启动工具两次"]
safeguards: ["用户在已知上一候选未通过后明确要求用当前roll0.5配置重新启动；此次只执行运行，不重开控制调参", "fresh，无resume/warm-start；保留旧模型日志及既有代码", "record PID+命令，重复执行验证不重启", "14项CPU与此前revision15更新恢复检查已通过，运行中验证新checkpoint的实际参数与优化器更新", "训练持续留在后台；启动验收与后续学习效果分开报告"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

此次是用户新指令下的正式运行操作，不是先前失败控制调参任务重试。无需重新请求授权，不改生产参数；验收以实际运行及checkpoint为准。
