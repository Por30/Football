---
task_id: "carrybox-convergence-20261015"
language: "zh-CN"
axes: ["L", "E", "C"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["docs/carrybox/convergence_20261015", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-convergence-20261015.md", "agent/task/carrybox-convergence-20261015.md", "agent/report/carrybox-convergence-20261015.md", "agent/handoff/carrybox-convergence-20261015.md"]
original_request: "训练还是收敛上去 你排下下下是什么原因"
development_modes: ["ML_TRAINING", "SIMULATOR_EXTENSION"]
forbidden_scope: ["修改生产源码/数据/训练配方", "停止或重启正式训练", "修改足球、共享资产或观测信息边界"]
steps: ["只读核验实时进程、日志和checkpoint", "提取训练分阶段趋势并核验AMP/奖励实现", "16环境有界纯推理对照，记录初始化和分技能失败", "区分已证实问题与待验证因果，更新项目记录"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/convergence_20261015/analyze.py"}, {"command": "bash docs/carrybox/convergence_20261015/replay.sh"}]
stop_conditions: ["资源不足或GPU错误立即停止诊断进程，保留正式训练", "测试两次修复仍失败", "需要修改生产代码则另行明确范围", "no controlled retraining, cannot quantify individual causal contributions"]
safeguards: ["不更新策略/优化器，不停止正式训练", "训练统计与推理成功率分开，短测不证明收敛", "16环境、最多3600policy steps，保持无特权actor/critic", "do not change production training", "separate observed conflict from causal contribution", "report per-skill/censored inference separately from training metrics", "read actual USD limits and official soft-limit formula"]
expert_required: true
expert_brief: {"affected_call_path": ["wall cfg/reset/rewards -> PPO/AMP -> checkpoint"], "critical_interfaces": ["USD soft knee limits versus expert reference", "weak warm-start and inherited log_std", "AMP separation versus valid windows"], "invariants": ["depth/proprio only actor/critic; pure proprio AMP; data/checkpoint unchanged"], "smallest_change_locus": ["diagnostic scripts and evidence only"], "mandatory_safeguards": ["do not change production training", "separate observed conflict from causal contribution", "report per-skill/censored inference separately from training metrics", "read actual USD limits and official soft-limit formula"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python docs/carrybox/convergence_20261015/analyze.py", "bash docs/carrybox/convergence_20261015/replay.sh"], "blockers": ["no controlled retraining, cannot quantify individual causal contributions"]}
device_actions: []
real_device_authorized: false
---

只读诊断当前wall4不收敛，以正式日志、数据检查及小规模推理给出可定位的原因；不修改或重启训练。