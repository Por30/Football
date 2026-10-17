---
task_id: "carrybox-wall5-length-20261016"
language: "zh-CN"
axes: ["E", "P", "L"]
risk_tier: "T2"
allowed_paths: ["docs/carrybox/wall5_length_20261016", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-length-20261016.md", "agent/task/carrybox-wall5-length-20261016.md", "agent/report/carrybox-wall5-length-20261016.md", "agent/handoff/carrybox-wall5-length-20261016.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "看一下当前v5训练 mean episode length上不去的原因是什么"
development_modes: ["ML_TRAINING", "SIMULATOR_EXTENSION"]
forbidden_scope: ["修改生产训练/数据/资产/奖励/阈值", "停止或重启正式训练", "用16环境短测替代正式成功率或声称全部根因已证实"]
steps: ["冻结正式log截至7249轮和model7200并核对指标定义", "统计分阶段日志及分技能累计差分", "严格加载同一checkpoint做16环境2x2动作采样/推扰四组各1200步回放", "分析终止前状态与存活回合并记录诊断边界", "更新项目入口及验证四工件"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_length_20261016/analyze.py"}, {"command": "bash docs/carrybox/wall5_length_20261016/replay.sh"}]
stop_conditions: ["可用显存不足4GiB则不启动回放", "严格checkpoint合同不匹配或任何非有限值立即停止诊断", "总计4800policy步，外层600秒超时，不升级为训练"]
safeguards: ["anchor0 iteration7200; four cases 1200 steps; exclude artificial case resets", "log push after reset against new episode, pre/post velocity; reset diagnostic counters", "nonpaired seeds after RNG divergence; 16env not formal success evidence", "separate raw action clipping and physical-target saturation; actual predicates vs overwritten log labels", "assert finite values, yaw7.2, full push scale before cases", "completed count equals done count; sum completed lengths plus censored ages equals19200 each case", "record initial states/reset samples/push count and raw episodes"]
expert_required: true
expert_brief: {"affected_call_path": ["Wall5 step -> termination/reward -> reset -> interval push -> obs; strict load does not restore curriculum"], "critical_interfaces": ["Mean episode length last100 completed; Skill means lifetime; termination logs mean per-env last retained label, not completed-episode fraction", "tipped actual root roll/pitch; fell root/head COM; success does not reset"], "invariants": ["strict schema2/rev9 load; no optimizer calls; unchanged depth/proprio/RSI/physics except diagnostics push/action sampling", "2x2 groups retain depth noise; separate completed and censored"], "smallest_change_locus": ["docs-only replay wrapping reset and registered interval event after strict load"], "mandatory_safeguards": ["anchor0 iteration7200; four cases 1200 steps; exclude artificial case resets", "log push after reset against new episode, pre/post velocity; reset diagnostic counters", "nonpaired seeds after RNG divergence; 16env not formal success evidence", "separate raw action clipping and physical-target saturation; actual predicates vs overwritten log labels"], "minimal_tests": ["assert finite values, yaw7.2, full push scale before cases", "completed count equals done count; sum completed lengths plus censored ages equals19200 each case", "record initial states/reset samples/push count and raw episodes"], "blockers": ["no direct termination-count bug found; logs alone do not isolate causal factors"]}
device_actions: []
real_device_authorized: false
---

T2诊断由一个E/P/L只读审查代理提供brief。两条冻结命令仅解析已有日志/CPU checkpoint及短时GPU推理，无优化器更新。生产4096训练保持运行，短测期间吞吐不作性能回归证据。结果保存在docs/carrybox/wall5_length_20261016。
