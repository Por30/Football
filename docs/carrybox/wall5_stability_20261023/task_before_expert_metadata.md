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
safeguards: ["固定13200与已能行走rev22模型同起点诊断，标注权重迁移非严格恢复", "一次验证一组改动，保留自碰撞、完整pickup、深度/critic/辅助监督及roll0.5语义，除非直接证据要求局部调整", "新行为更改revision/契约，旧ckp不静默恢复；GPU短训只写docs", "保持历史数据、正式模型和未提交改动；新训练fresh4096/seed42"]
expert_required: true
device_actions: []
real_device_authorized: false
---

核对空手快速倾倒的机械/控制及学习采样原因，以rev22为行为对照，不把相同力矩配置或低style直接判为根因。修复最小有证据的问题，短测通过后按用户授权从零重启4096环境正式训练。
