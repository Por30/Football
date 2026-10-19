---
task_id: "carrybox-wall5-reset-bug-20261019"
language: "zh-CN"
axes: ["E", "C", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "停掉当前训练重新排查bug，判断失稳摔倒reset原因，修复后重新启动训练，并完整解释wall5从观测到奖励的训练设计。"
development_modes: ["ML_TRAINING", "SIMULATOR_EXTENSION"]
allowed_paths: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "tests/test_carrybox_reset_bug.py", "docs/carrybox/wall5_reset_bug_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-reset-bug-20261019.md", "agent/task/carrybox-wall5-reset-bug-20261019.md", "agent/report/carrybox-wall5-reset-bug-20261019.md", "agent/handoff/carrybox-wall5-reset-bug-20261019.md"]
forbidden_scope: ["不改共享资产/PD/深度/数据/足球任务接口/roll阈值", "不恢复已失败的静态PD候选，不删除历史数据、模型或工作区改动", "不把工程PASS或持箱存活宣称为找箱行走/拾箱成功"]
steps: ["记录原进程已退出并锁定6600诊断证据", "实现仅wall5反馈、动作分布与固定采样修复", "执行CPU与4环境更新恢复导出检查", "执行512环境200轮fresh有界pilot并报告行为", "检查资源后从零启动4096正式训练并核验速度和契约", "记录完整设计、结果和项目状态"]
tests: [{"command": "bash docs/carrybox/wall5_reset_bug_20261019/check.sh"}, {"command": "bash docs/carrybox/wall5_reset_bug_20261019/smoke.sh"}, {"command": "bash docs/carrybox/wall5_reset_bug_20261019/pilot.sh"}]
stop_conditions: ["NaN/OOM/interface/gradient/timeout/quota errors", "two in-scope failed-check repairs maximum; no relaxed assertions", "short pilot does not establish walking or lifting success"]
safeguards: ["failure=-1 raw per terminal step, no timeout/leak", "inward mean-bound gradient and per-minibatch std cap", "ground-relative height, near-box crouch exemption, no horizontal zero-speed or anchor reward", "no privileged labels into actor/critic/export", "fresh formal4096 and old models retained; no convergence claim from smoke"]
expert_required: true
expert_brief: {"affected_call_path": ["wall5 reset → physical targets → task rewards → PPO/AMP; latest6600 first episodes and reward units verified"], "critical_interfaces": ["raw Normal likelihood unchanged; action-bound labels training-only; done GAE already correct"], "invariants": ["actor372+depth4x27x48, critic108, AMP600/data13; original PD, physics, depth, roll0.5/pitch1.1", "80/20 fixed env quotas differ from independent reset probabilities; preserve RSI source motion"], "smallest_change_locus": ["wall5 rewards, skill assignment, bounds/std; shared hooks preserve old defaults"], "mandatory_safeguards": ["failure=-1 raw per terminal step, no timeout/leak", "inward mean-bound gradient and per-minibatch std cap", "ground-relative height, near-box crouch exemption, no horizontal zero-speed or anchor reward", "no privileged labels into actor/critic/export", "fresh formal4096 and old models retained; no convergence claim from smoke"], "minimal_tests": ["bash docs/carrybox/wall5_reset_bug_20261019/check.sh", "bash docs/carrybox/wall5_reset_bug_20261019/smoke.sh", "bash docs/carrybox/wall5_reset_bug_20261019/pilot.sh"], "blockers": ["NaN/OOM/interface/gradient/timeout/quota errors", "two in-scope failed-check repairs maximum; no relaxed assertions", "short pilot does not establish walking or lifting success"]}
device_actions: []
real_device_authorized: false
---

专家只读审计已完成。三条测试冻结；baseline三组32环境已在改代码前执行，check仅审计原始证据。pilot仅验证有界学习过程并如实报告行为，正式启动仍需资源和首模型检查。
