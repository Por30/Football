---
task_id: "carrybox-walled-g1"
language: "zh-CN"
axes: ["E", "P", "L", "D"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["SIMULATOR_EXTENSION", "ML_TRAINING", "SENSOR_DRIVER"]
original_request: "将用户提供的 X2 FindBox walled3/walled4 说明迁移为本地 G1 继承变体，解释观测、输出和任务设计，提供启动命令。保留无特权 actor/critic、位姿监督和 FindBox AMP。"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/carrybox_walled.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/smoke_carrybox_walled.py", "scripts/rsl_rl/smoke_carrybox_walled.sh", "tests/test_carrybox_walled.py", "docs/carrybox", "projects", "README.md", "agent"]
forbidden_scope: ["修改原始动作/资产/足球训练接口", "长期训练或操作足球进程", "真实硬件", "策略/价值读取箱子真值或阶段"]
steps: ["冻结迁移差异与接口", "实现继承场景及参考初始化", "实现传感器配对扰动和课程/奖励", "集成训练与checkpoint边界", "执行CPU及真实RTX短测", "更新项目设计、命令及交接"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}, {"command": "bash scripts/rsl_rl/smoke_carrybox_walled.sh"}, {"command": "bash scripts/rsl_rl/smoke_carrybox.sh"}]
stop_conditions: ["两次范围内修复后冻结验收仍失败", "数据schema或关节映射不能验证", "需要长期训练或真实硬件"]
safeguards: ["深度与监督标签配对延迟及冻结，reset不跨回合", "课程仅使用实际训练迭代并按进程建立锚点", "不同变体checkpoint禁止隐式混用", "原始数据只读，RSI与AMP样本概率分离", "真实碰撞和RTX可见性短测"]
expert_required: true
device_actions: []
real_device_authorized: false
expert_brief: {"affected_call_path": ["变体Gym ID→继承配置→CarryBox子类→独立MDP→现有PPO/AMP runner"], "critical_interfaces": ["actor/critic:372+4x27x48; labels9监督; AMP640判别器", "XY ZW参考四元数与命名关节映射；box_pos_local为世界朝向root位移"], "invariants": ["不把真值/技能/search加入策略价值；不改足球", "reset机器人→箱子平台→墙→柱；无成功终止或虚构torque限制"], "smallest_change_locus": ["独立walled配置/MDP/张量helper，基线仅terminal接口和runner变体钩子"], "mandatory_safeguards": ["深度与监督标签配对延迟及冻结，reset不跨回合", "课程仅使用实际训练迭代并按进程建立锚点", "不同变体checkpoint禁止隐式混用", "原始数据只读，RSI与AMP样本概率分离", "真实碰撞和RTX可见性短测"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "bash scripts/rsl_rl/smoke_carrybox_walled.sh", "bash scripts/rsl_rl/smoke_carrybox.sh"], "blockers": []}
---

按用户规格新增 G1 walled3 和继承它的 walled4。保留基线与足球接口。X2 完整源码未提供，父奖励沿用本地已验证 G1 基线；未指定的传感器扰动幅度显式记录为本地参数。只运行有限短测。

只读组合专家的非阻塞未知项已转为明确迁移差异：X2父奖励/扰动幅度缺失，箱子姿态/putDown缺失；参考箱子保直立，显式weights-only跨变体。成功采用每回合一次奖励；障碍可见测试移入3m量程。完整验证结果如失败则不宣称可训练。
