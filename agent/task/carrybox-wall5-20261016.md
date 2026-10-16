---
task_id: "carrybox-wall5-20261016"
language: "zh-CN"
axes: ["L", "E"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/train_carrybox_walled.sh", "tests/test_carrybox_wall5.py", "docs/carrybox/wall5_20261016", "README.md", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-20261016.md", "agent/task/carrybox-wall5-20261016.md", "agent/report/carrybox-wall5-20261016.md", "agent/handoff/carrybox-wall5-20261016.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "/home/cao/perceptual_ball/x2g1differ.md 根据这个differ 在wall4任务基础上修改成wall5 然后给我wall5和wall4 你做了哪些动动说明"
development_modes: ["ML_TRAINING", "ML_DATA_PIPELINE", "SIMULATOR_EXTENSION", "SYSTEM_TUNING"]
forbidden_scope: ["改变Wall4/足球学习行为或共享资产", "修改原始动作数据", "加入特权critic或箱子真值AMP", "启动或停止正式训练", "把短测当收敛"]
steps: ["确认差异与冻结阶段A范围", "新增隔离Wall5 AMP及环境/任务入口", "验证在线专家特征、首步终止、奖励与恢复边界", "4环境完整更新、重建恢复与导出短测", "更新对照说明及项目入口"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}, {"command": "bash docs/carrybox/wall5_20261016/validate.sh"}]
stop_conditions: ["同一测试两次修复仍失败", "短测显存不足或影响已有任务安全", "非有限状态且不能在范围内修复"]
safeguards: ["Wall4及足球行为不变；actor/critic只用深度本体，AMP纯本体", "AMP完整恢复双向拒绝Wall4/Wall5混用，包括load_optimizer=False", "显式policy-only仅迁移同形策略；D/优化器全新，不默认使用旧策略", "statistics_initialized在Wall5表示固定原始特征管线就绪，不表示专家统计归一化", "固定lr、weight decay、初始化、梯度惩罚明确记录，不声称完全复现X2或解决饱和", "P0是AMP多因素一组修订，不归因单个因素使策略收敛；P1/P2后续", "历史每步只追加一次、reset只清对应环境、terminal与新首帧分开", "保留现有进程，仅4环境短测，不启动或停止正式训练"]
expert_required: true
expert_brief: {"affected_call_path": ["Wall5独立Gym/config/env/runner→35维AMP在线与专家→终止history→PPO/AMP更新、恢复、导出"], "critical_interfaces": ["10×35，在线/专家顺序一致；RSI速度保留；首次append重复首帧；绕过归一化及clamp；无dt AMP"], "invariants": ["Wall4和足球不变；本体+深度策略；PPO/奖励几何/RSI不变"], "smallest_change_locus": ["Wall5子类，最小注册/runner分支；扩大yaw枚举；有效窗口指标按变体"], "mandatory_safeguards": ["Wall4及足球行为不变；actor/critic只用深度本体，AMP纯本体", "AMP完整恢复双向拒绝Wall4/Wall5混用，包括load_optimizer=False", "显式policy-only仅迁移同形策略；D/优化器全新，不默认使用旧策略", "statistics_initialized在Wall5表示固定原始特征管线就绪，不表示专家统计归一化", "固定lr、weight decay、初始化、梯度惩罚明确记录，不声称完全复现X2或解决饱和", "P0是AMP多因素一组修订，不归因单个因素使策略收敛；P1/P2后续", "历史每步只追加一次、reset只清对应环境、terminal与新首帧分开", "保留现有进程，仅4环境短测，不启动或停止正式训练"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "bash docs/carrybox/wall5_20261016/validate.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

依照x2g1differ.md第6节阶段A实施P0组：AMP幅度、特征、正则化与首步窗口。保持PPO、4帧深度、共享critic、RSI、物理任务与15段原始数据不变，便于对照；P1/P2明确留待后续，不启动正式训练。
