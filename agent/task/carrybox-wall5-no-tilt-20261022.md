---
task_id: "carrybox-wall5-no-tilt-20261022"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "去掉倾斜reset的逻辑把 和phsi保持一直 然后重启训练"
development_modes: ["SYSTEM_TUNING", "ML_TRAINING"]
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "docs/carrybox/wall5_no_tilt_20261022", "projects/README.md", "projects/findbox/README.md", "logs/rsl_rl/g1_carrybox_depth/walled5", "agent/plan/carrybox-wall5-no-tilt-20261022.md", "agent/task/carrybox-wall5-no-tilt-20261022.md", "agent/report/carrybox-wall5-no-tilt-20261022.md", "agent/handoff/carrybox-wall5-no-tilt-20261022.md"]
forbidden_scope: ["不改foot接地、奖励、碰撞、RSI、actor/critic/AMP或数据", "不改wall3/wall4/football、共享接口、PhysHSI源代码", "不删历史模型，不操作实机"]
steps: ["核对PhysHSI与当前进程，保存源码及模型身份", "仅wall5禁用倾斜终止并记录revision25与诊断语义", "仿真验证大倾角不触发reset、保留终止仍有效，以及一次PPO/AMP更新和checkpoint恢复", "停止身份匹配旧进程，从头启动4096并确认训练推进和首模型", "更新入口及工程回执"]
tests: [{"command": "bash docs/carrybox/wall5_no_tilt_20261022/smoke.sh"}, {"command": "bash docs/carrybox/wall5_no_tilt_20261022/start_and_verify.sh"}]
stop_conditions: ["修改范围升级或进程身份不符", "验证非有限或严重物理错误", "冻结测试失败最多两次原范围修复"]
safeguards: ["保留20s超时、非有限状态检查、三个高度和箱速终止", "PhysHSI实际有roll/pitch终止，本次明确按用户要求取消，不声称完全相同", "旧模型拒绝作为revision25严格恢复；从零启动，验证模型不进入正式run", "倾斜只在回合结束统计，不误称reset原因", "先短测通过再停旧训练，保存历史模型和日志"]
expert_required: false
device_actions: []
real_device_authorized: false
---

仅wall5取消roll/pitch直接终止，保留其他PhysHSI高度/箱速条件与20秒超时。当前PhysHSI也含角度终止，因此本次为用户明确指定的例外，不称完全一致。变更checkpoint契约并验证后重启4096从头正式训练；足底穿地等诊断事项保留为后续，不混入本轮参数调整。
