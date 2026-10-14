---
task_id: "carrybox-wall4-restart-20261014"
language: "zh-CN"
axes: ["A"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["agent", "docs/carrybox/restart_20261014", "projects/README.md", "projects/findbox/README.md", "README.md", "logs/rsl_rl/g1_carrybox_depth/walled4"]
original_request: "重新启动训练"
forbidden_scope: ["修改机器人控制/奖励/数据或足球", "删除旧模型与日志", "恢复旧等待器或重复启动"]
development_modes: ["ML_TRAINING"]
steps: ["核实资源、旧进程与奖励回归", "从头启动唯一新wall4进程并记录身份", "核查正式迭代和checkpoint以及早期AMP指标", "同步项目入口及交接"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox_convergence.py -v"}]
stop_conditions: ["启动失败或CUDA/非有限故障时停止并报告", "不将短时运行当作收敛结论"]
safeguards: ["只启动仿真训练，无实机", "新目录保存，旧模型只读，根findbox数据不改", "用户最新启动指令覆盖旧文档的停止要求；动作范围问题保留记录"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

重新启动既有已修复配置属于运行操作；动作范围问题未修复，不能宣称完整问题已解决。旧checkpoint环境revision3不用于新revision4恢复。
