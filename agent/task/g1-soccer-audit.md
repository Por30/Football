---
task_id: "ENG-G1-SOCCER-AUDIT-20260919"
artifact: "TASK"
status: "FROZEN"
language: "zh-CN"
axes: ["L", "P", "D", "C"]
development_modes: ["ML_TRAINING", "STATE_MACHINE", "MODEL_DEPLOYMENT"]
risk_tier: "T1"
original_request: "G1 你看一下现在soccer任务 有什么可以改进的地方"
allowed_paths: ["docs/research/iros2027", "agent"]
forbidden_scope: ["修改训练与任务实现", "改动已有 checkpoint", "启动长期训练或真实设备", "把离线反例描述为性能结果"]
steps: ["核对 Soccer v2 与依赖调用链", "读取 AMP 数据与现有 checkpoint", "构造源码绑定的 CPU 离线探针", "记录优先级、影响与改进建议", "更新 G1 平台记录并校验工件"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/research/iros2027/audit_soccer_cpu.py"}]
stop_conditions: ["必要验证需要修改训练代码或启动真实设备", "连续两次无法完成离线探针则报告限制"]
safeguards: ["全部张量在 CPU", "不改变任务与 checkpoint", "离线构造状态与仿真结果明确区分", "结论绑定源码哈希"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

# G1 Soccer v2 审查任务

从当前任务、球状态机、AMP 特征/判别器、训练 runner、play 导出以及本地 Isaac Lab/RSL-RL 调用链读取证据。冻结测试检查审查结论能否复现；测试通过表示缺陷证据复现，不表示生产代码正确或策略性能达标。详细结果写入 `docs/research/iros2027/SOCCER_V2_AUDIT.md`。
