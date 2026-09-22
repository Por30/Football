---
task_id: "ENG-G1-SOCCER-V3-20260919"
language: "zh-CN"
axes: ["E", "P", "C", "L", "D", "S"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["ML_TRAINING", "STATE_MACHINE", "SIMULATOR_EXTENSION", "MODEL_DEPLOYMENT"]
original_request: "修复上述问题之后写好一个v3任务"
allowed_paths: ["source/perceptual_ball/perceptual_ball", "scripts/rsl_rl", "tests", "docs/research/iros2027", "agent"]
forbidden_scope: ["改动旧checkpoint/参考动作文件", "长期训练或实机运行", "论文创新/性能达标声明"]
steps: ["统一AMP特征及训练状态保存", "修复终止观测/接触/导出与偏置", "新增v3恢复目标任务和感知时序", "运行CPU回归与真实仿真smoke", "保存可运行说明与验证交接"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_soccer_v3.py"}, {"command": "bash scripts/rsl_rl/smoke_soccer_v3.sh"}]
stop_conditions: ["真实设备需求", "超出允许范围的破坏性改动", "测试失败两次后重新诊断而不放宽标准"]
safeguards: ["仅仿真和离线测试，不运行真实设备", "terminal历史不重复推进；仅存终止行并带env_ids", "脚球传感过滤为空或history不匹配立即报错，不退回距离代理", "所有发球结算一次；reset不可隐藏失败", "统一AMP特征和统计，保存全部训练分支", "aux行为KL约束与梯度裁剪", "发布任务与未训练性能明确区分"]
expert_required: true
expert_brief: {"affected_call_path": ["env physics -> state -> terminal snapshot -> reset -> PPO/AMP -> checkpoint/export"], "critical_interfaces": ["IsaacLab terminal reset ordering, ContactSensor [N,T,1,M,3], RSL-RL 3.0.1 save/load/timeouts"], "invariants": ["ordered 60D expert/live features, action-time skill, oldest-to-newest obs history", "full return requires valid strike + target + sustained recovery"], "smallest_change_locus": ["shared feature/algorithm/runner fixes plus independent SoccerV3 config/state/env/export"], "mandatory_safeguards": ["仅仿真和离线测试，不运行真实设备", "terminal历史不重复推进；仅存终止行并带env_ids", "脚球传感过滤为空或history不匹配立即报错，不退回距离代理", "所有发球结算一次；reset不可隐藏失败", "统一AMP特征和统计，保存全部训练分支", "aux行为KL约束与梯度裁剪", "发布任务与未训练性能明确区分"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_soccer_v3.py", "bash scripts/rsl_rl/smoke_soccer_v3.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

按组合轴专家接口审查执行。两条冻结命令内覆盖真实参考数据、构造边界、完整导出与 IsaacLab 物理接触/训练/恢复。资源不足时保留准确执行状态，不以 mock 替代仿真。
