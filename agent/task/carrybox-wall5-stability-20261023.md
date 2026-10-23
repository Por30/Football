---
task_id: "carrybox-wall5-stability-20261023"
language: "zh-CN"
axes: ["E", "C", "L"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_physhsi.py", "source/perceptual_ball/perceptual_ball/carrybox_physhsi.py", "source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "docs/carrybox/wall5_stability_20261023", "tests/test_carrybox_wall5_stability.py", "projects/README.md", "projects/findbox/README.md", "logs/rsl_rl/g1_carrybox_depth/walled5", "agent/plan/carrybox-wall5-stability-20261023.md", "agent/task/carrybox-wall5-stability-20261023.md", "agent/report/carrybox-wall5-stability-20261023.md", "agent/handoff/carrybox-wall5-stability-20261023.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "排查下空手站立快速倾倒的原因 然后重新启动训练 不应该连站立和走路都学不会吧"
development_modes: ["SIMULATOR_EXTENSION", "ML_TRAINING", "SYSTEM_TUNING"]
forbidden_scope: ["不更改足球、共享资产、通用PPO/AMP/观测接口", "不改数据/删模型，不无证据改力矩惩罚或放宽终止", "不将短测写成行走/拾箱收敛，不操作真实硬件"]
steps: ["冻结正式状态，复核空手/持箱采样与同初态策略对照", "组合轴专家只读审查；按证据选择最小修复并记录前后", "针对性CPU、仿真更新恢复与有限短训/回放验证", "验证通过后停止旧wall5，4096环境从零正式启动并检查多轮", "更新报告、交接及项目入口"]
tests: [{"command": "bash docs/carrybox/wall5_stability_20261023/diagnose.sh"}, {"command": "bash docs/carrybox/wall5_stability_20261023/validate.sh"}, {"command": "bash docs/carrybox/wall5_stability_20261023/start_and_verify.sh"}]
stop_conditions: ["身份不一致、非有限值或显存不足则停依赖操作", "每条冻结测试失败最多两次原范围修复，保留证据", "正式启动前确保旧进程退出且验证通过；禁止重复启动"]
safeguards: ["固定13200与已能行走rev22模型同起点诊断，标注权重迁移非严格恢复", "一次验证一组改动，保留自碰撞、完整pickup、深度/critic/辅助监督及roll0.5语义，除非直接证据要求局部调整", "新行为更改revision/契约，旧ckp不静默恢复；GPU短训只写docs", "保持历史数据、正式模型和未提交改动；新训练fresh4096/seed42", "四类来源全固定但不限制任务内阶段；每回合参考帧/扰动仍随机，标签不得进入actor/critic", "生存项使用标准is_alive，仅一次dt缩放；失败步为0，纯timeout为1，不增加蹲姿限制", "保留quota-only和alive1失败证据，按相同512/128/seed比较；不降低行为断言，不以总体奖励替代空手指标", "同冻结AMP旧策略混合回报更高；不得把raw task排序或负均值单独当作完整目标偏好倾倒的证据", "alive3通过既定行为断言后不继续增大权重；短期改善不等于学会站走拾箱"]
expert_required: true
device_actions: []
real_device_authorized: false
expert_brief: {"affected_call_path": ["wall5 hybrid初始化来源分配 → reset_scene → on-policy控制步采样；RewardManager is_alive → .75 task+.125 style"], "critical_interfaces": ["按全局env_id分区、读取实际cfg；default日志使用step前标签；AMP使用真实终止前窗口；checkpoint记录全部行为变更"], "invariants": ["保持完整三pickup、自碰撞/接地/PD/动作延迟和roll0.5，actor深度本体、critic123和辅助监督保持"], "smallest_change_locus": ["四个wall5文件：固定四来源、标签时序及cfg/契约；alive1未通过后仅将同一权重调整为3并重复同一短训"], "mandatory_safeguards": ["四类来源全固定但不限制任务内阶段；每回合参考帧/扰动仍随机，标签不得进入actor/critic", "生存项使用标准is_alive，仅一次dt缩放；失败步为0，纯timeout为1，不增加蹲姿限制", "保留quota-only和alive1失败证据，按相同512/128/seed比较；不降低行为断言，不以总体奖励替代空手指标", "同冻结AMP旧策略混合回报更高；不得把raw task排序或负均值单独当作完整目标偏好倾倒的证据", "alive3通过既定行为断言后不继续增大权重；短期改善不等于学会站走拾箱"], "minimal_tests": ["bash docs/carrybox/wall5_stability_20261023/diagnose.sh", "bash docs/carrybox/wall5_stability_20261023/validate.sh", "bash docs/carrybox/wall5_stability_20261023/start_and_verify.sh"], "blockers": ["身份不一致、非有限值或显存不足则停依赖操作", "每条冻结测试失败最多两次原范围修复，保留证据"]}
---

核对空手快速倾倒的机械/控制及学习采样原因，以rev22为行为对照，不把相同力矩配置或低style直接判为根因。修复最小有证据的问题，短测通过后按用户授权从零重启4096环境正式训练。