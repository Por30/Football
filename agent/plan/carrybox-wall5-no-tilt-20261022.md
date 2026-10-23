---
task_id: "carrybox-wall5-no-tilt-20261022"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "PLAN"
status: "READY"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "docs/carrybox/wall5_no_tilt_20261022", "projects/README.md", "projects/findbox/README.md", "logs/rsl_rl/g1_carrybox_depth/walled5", "agent/plan/carrybox-wall5-no-tilt-20261022.md", "agent/task/carrybox-wall5-no-tilt-20261022.md", "agent/report/carrybox-wall5-no-tilt-20261022.md", "agent/handoff/carrybox-wall5-no-tilt-20261022.md"]
---

仅wall5取消roll/pitch直接终止，保留其他PhysHSI高度/箱速条件与20秒超时。当前PhysHSI也含角度终止，因此本次为用户明确指定的例外，不称完全一致。变更checkpoint契约并验证后重启4096从头正式训练；足底穿地等诊断事项保留为后续，不混入本轮参数调整。
