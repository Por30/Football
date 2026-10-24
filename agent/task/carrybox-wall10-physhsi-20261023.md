---
task_id: "carrybox-wall10-physhsi-20261023"
language: "zh-CN"
axes: ["L", "D", "C", "P"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall10_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/play_carrybox_walled.sh", "tests/test_carrybox_wall10.py", "docs/carrybox/wall10_20261023", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall10-physhsi-20261023.md", "agent/task/carrybox-wall10-physhsi-20261023.md", "agent/report/carrybox-wall10-physhsi-20261023.md", "agent/handoff/carrybox-wall10-physhsi-20261023.md"]
artifact: "TASK"
status: "FROZEN"
development_modes: ["ML_TRAINING", "SIMULATOR_EXTENSION", "STATE_MACHINE"]
original_request: "新建findbox wall10任务 从phsi的搬箱子任务迁移到这里来 保持原有训练细节的同时 根据本项目findbox任务更改 原有的任务流程 观测仍然使用非对称ac actor用深度信息代替 然后把任务流程缩短 只需要把箱子搬起来原地站著就可以 你完成新的任务后讲一下任务的实现和细节"
forbidden_scope: ["修改足球及wall3/4/5行为", "修改共享G1资产或原动作数据", "停止或启动正式训练", "真实设备操作", "无关清理"]
steps: ["核对PhysHSI源配置与本地调用链，记录保留项与必要适配", "新增独立wall10配置、缩短任务及深度非对称观测", "迁移原训练配方、控制随机化和checkpoint契约", "执行CPU定向检查及小规模仿真更新恢复导出", "更新项目入口、看板、Report和Handoff并验证工件"]
tests: [{"command": "bash docs/carrybox/wall10_20261023/validate_cpu.sh"}, {"command": "bash docs/carrybox/wall10_20261023/validate_sim.sh"}]
stop_conditions: ["需修改冻结范围之外生产路径", "两次范围内修复后冻结测试仍失败", "资源不足以安全运行短测"]
safeguards: ["actor和导出不得读取特权状态", "不改既有任务的配置与checkpoint身份", "partial reset历史和terminal AMP保持正确", "有限值、物理力矩限幅、失败终止保持", "不操作现有正式训练"]
expert_required: true
device_actions: []
real_device_authorized: false
expert_brief: {"affected_call_path": ["wall10 Gym -> train/play -> independent config/MDP/runner -> PPO+AMP"], "critical_interfaces": ["PPO100,5x4,1e-3 adaptive; shared Adam AC+AMP; no Normalizer; smooth policy1/9 value1/90; AMP60x10; explicit PD and motor effort limits"], "invariants": ["actor depth/proprio only, critic123 independent and goal removed", "PhysHSI torque/Kp penalty, source reset and randomized PD"], "smallest_change_locus": ["four new wall10 modules and additive registration/dispatch"], "mandatory_safeguards": ["actor和导出不得读取特权状态", "不改既有任务的配置与checkpoint身份", "partial reset历史和terminal AMP保持正确", "有限值、物理力矩限幅、失败终止保持", "不操作现有正式训练"], "minimal_tests": ["bash docs/carrybox/wall10_20261023/validate_cpu.sh", "bash docs/carrybox/wall10_20261023/validate_sim.sh"], "blockers": []}
---

新增独立wall10，从本地PhysHSI G1搬箱任务迁移；保留原训练细节，actor以FindBox深度替代真值任务信息，critic保留训练专用真值。流程止于抬箱后原地保持，取消搬运目标和放下；短测工件只进入docs，不启动正式长训。
