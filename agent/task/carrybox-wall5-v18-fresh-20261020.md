---
task_id: "carrybox-wall5-v18-fresh-20261020"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "停止当前训练然后重启从头开始新的训练"
development_modes: ["ML_TRAINING"]
allowed_paths: ["docs/carrybox/wall5_v18_fresh_20261020", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-v18-fresh-20261020.md", "agent/task/carrybox-wall5-v18-fresh-20261020.md", "agent/report/carrybox-wall5-v18-fresh-20261020.md", "agent/handoff/carrybox-wall5-v18-fresh-20261020.md"]
forbidden_scope: ["不改已通过验证的revision18源码/超参/数据或足球任务", "不恢复旧模型/优化器/课程，不删除旧日志模型或已有工作区改动", "不将正式启动核验作为收敛或抱箱能力证明"]
steps: ["核对旧训练身份并停止，保留历史模型", "确认revision18验证记录、源码hash、数据和资源后启动4096 fresh正式run", "核对首模型新契约/全新优化器和Normalizer，确认日志迭代推进及耗时", "更新项目状态、结果和交接记录"]
tests: [{"command": "bash docs/carrybox/wall5_v18_fresh_20261020/verify.sh"}]
stop_conditions: ["训练身份不一致或资源不足不重复启动", "发现NaN/OOM/源码变化/错误契约立即报告并只在授权范围内处理", "最多两次范围内测试修复，不放宽断言"]
safeguards: ["仅对匹配PID完整命令的旧wall5发终止信号", "正式4096、seed42、40000轮，从零无resume/warm-start", "复用43项CPU及4环境更新检查；校验源码hash与首checkpoint", "记录精确进程、日志和新run；验证参数/优化器有限值及最近10轮每轮≤6s"]
expert_required: false
device_actions: []
real_device_authorized: false
---

仅运行已验证任务，不调参。启动前比对revision18测试证据与源码hash；正式运行的首checkpoint/优化器及连续日志作为集成验收，校验模块和数据身份作为针对性检查。所有新工件与旧记录分目录。
