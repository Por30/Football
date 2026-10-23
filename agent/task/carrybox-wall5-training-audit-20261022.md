---
task_id: "carrybox-wall5-training-audit-20261022"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "看看在在还有没有什么 训练上的硬伤或者bug"
development_modes: ["ML_TRAINING"]
allowed_paths: ["docs/carrybox/wall5_training_audit_20261022", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-training-audit-20261022.md", "agent/task/carrybox-wall5-training-audit-20261022.md", "agent/report/carrybox-wall5-training-audit-20261022.md", "agent/handoff/carrybox-wall5-training-audit-20261022.md"]
forbidden_scope: ["不修改生产源码、正式配置、数据或模型", "不停止/重启/调参正式训练，不操作真实设备", "不将短测或推断写成收敛结论"]
steps: ["冻结进程/源身份/现有checkpoint与日志", "审查PPO/AMP、观测、奖励及reset端实际代码与配置", "只读回放量化奖励惩罚、AMP历史/特征对照及策略动作，运行针对性CPU合同", "分级记录确定问题与待验证风险，验证来源和进程保持", "更新报告与项目入口"]
tests: [{"command": "bash docs/carrybox/wall5_training_audit_20261022/check.sh"}]
stop_conditions: ["生产源/训练进程身份改变则停止依赖检查", "非有限值或GPU资源不足则停止回放并报告", "测试失败最多两次原范围修复，保留失败证据"]
safeguards: ["固定checkpoint只读，不更改policy/AMP权重或normalizer", "使用日志累计计数差估计近期回合，不把Episode_Termination标签当作近期比例", "正式训练与诊断样本分开，写明步数/单位/技能分母", "检查源码和实测证据再定bug，用户明确选择的辅助设置标为风险而非擅自撤销"]
expert_required: false
device_actions: []
real_device_authorized: false
---

对正在运行的wall5 revision26做只读训练审查。核对实际代码、保存配置和固定checkpoint，使用针对性CPU合同和有限回放验证疑点；不调整生产或训练状态。输出可复核的严重度、证据、后果和建议，区分确定bug、设计风险和已检查正常项。
