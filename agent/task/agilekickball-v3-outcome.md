---
task_id: "AGILE-V3-OUTCOME-20261003"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "在v2的基础上 尝试加上一些创新 新建v3任务 然后给我训练的令令 明明明你做了些些改动"
development_modes: ["ML_TRAINING", "SIMULATOR_EXTENSION"]
allowed_paths: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/contact_outcome.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "tests/test_contact_outcome.py", "tests/test_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "scripts/rsl_rl/train_agilekickball_v3.sh", "docs/agilekickball_v3/README.md", "docs/agilekickball_v3/outcome_20261003", "README.md", "agent/plan/agilekickball-v3-outcome.md", "agent/task/agilekickball-v3-outcome.md", "agent/report/agilekickball-v3-outcome.md", "agent/handoff/agilekickball-v3-outcome.md"]
forbidden_scope: ["改变 v2 行为或改奖励/发球节奏", "长时间正式训练和真实机器人操作", "改写历史 checkpoint 或历史验证结果", "生成式 tracking、反事实世界模型及候选蒸馏架构扩展"]
steps: ["读取现状并冻结数据/训练边界", "实现 v3 后果辅助及训练期标签", "添加 checkpoint 预检查与独立启动脚本", "完成针对性回归及有限仿真", "说明变更、训练命令与限制并校验工件"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_contact_outcome.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v3.sh"}]
stop_conditions: ["同一冻结测试两次范围内修复后仍失败", "需要扩大允许范围或真实设备权限"]
safeguards: ["先按时间和环境构造 t+8 标签，再随机取样；剔除窗口内 done、发球变化和不完整尾部。", "空样本明确跳过，非有限样本屏蔽并计数；不制造零标签。", "独立 outcome 阶段监控 batch 与固定 monitor 的 KL；回退同时恢复参数和 Adam 动量，失败仅更新头。", "训练计数使用 float64，避免 float32 累计计数精度损失。", "推理仅使用原视觉和本体；真值训练组不进入 actor/critic 或导出。", "旧 revision、缺失恢复 optimizer、配置不匹配在加载模型前拒绝。", "只运行有限单元和仿真 smoke，不启动正式长训、不覆盖历史记录。", "保留 v2 行为与 v3 3m/±0.35m/1.2m 空间要求；proxy 不称真实接触，短时姿态不称恢复成功。"]
expert_required: true
expert_brief: {"affected_call_path": ["v3 train-only observation -> ordered rollout -> future targets -> outcome auxiliary -> shared encoder", "v3 config -> runner -> optional checkpoint outcome state"], "critical_interfaces": ["obs[t] precedes action[t]; target obs[t+8], no done in transitions t..t+7", "future ball velocity expressed in source yaw frame; future gravity in future body frame; height above env origin", "outcome head takes deployable actor features + detached current action only"], "invariants": ["v2 reward/control/PPO/AMP unchanged; v3 geometry unchanged", "proxy and short-horizon on-policy outcome semantics remain explicit"], "smallest_change_locus": ["new contact_outcome.py subclasses/helpers", "v3 config/state observation, optional runner checkpoint hooks, focused tests and documentation"], "mandatory_safeguards": ["先按时间和环境构造 t+8 标签，再随机取样；剔除窗口内 done、发球变化和不完整尾部。", "空样本明确跳过，非有限样本屏蔽并计数；不制造零标签。", "独立 outcome 阶段监控 batch 与固定 monitor 的 KL；回退同时恢复参数和 Adam 动量，失败仅更新头。", "训练计数使用 float64，避免 float32 累计计数精度损失。", "推理仅使用原视觉和本体；真值训练组不进入 actor/critic 或导出。", "旧 revision、缺失恢复 optimizer、配置不匹配在加载模型前拒绝。", "只运行有限单元和仿真 smoke，不启动正式长训、不覆盖历史记录。", "保留 v2 行为与 v3 3m/±0.35m/1.2m 空间要求；proxy 不称真实接触，短时姿态不称恢复成功。"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_contact_outcome.py", "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py", "bash scripts/rsl_rl/smoke_agilekickball_v3.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

唯一 P+L 专家完成只读接口审查。已吸收两项实现前置：smoke rollout 从 8 改为正式 24 步；旧等价断言精确排除新增训练观测和 policy/algorithm 后比较其余配置。0.16 s 未来为随后 rollout 策略下的统计结果，不用于在线反事实动作评价。
