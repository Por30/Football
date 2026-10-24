---
task_id: "carrybox-physhsi-full-audit-20261023"
language: "zh-CN"
axes: ["L", "C", "E", "P"]
risk_tier: "T2"
allowed_paths: ["docs/carrybox/physhsi_full_audit_20261023", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-physhsi-full-audit-20261023.md", "agent/task/carrybox-physhsi-full-audit-20261023.md", "agent/report/carrybox-physhsi-full-audit-20261023.md", "agent/handoff/carrybox-physhsi-full-audit-20261023.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "你再仔细比对以下当前任务细节和 /home/cao/PhysHSI/legged_gym/resources 下的搬箱子任务有什么区别 把所有细节都对比出来 我们要重构当前任务"
development_modes: ["ML_TRAINING", "ML_DATA_PIPELINE", "CONTROL_LOOP"]
forbidden_scope: ["不修改生产代码、数据、资产、模型或训练状态", "不将静态差异当成已证明失稳根因", "不把独立wall10短测当作正式收敛证据"]
steps: ["锁定wall5、PhysHSI carrybox/carrybox_resume及resources来源身份", "逐层核对观测控制资产场景reset终止和随机化", "核对全部有效奖励、AMP、PPO、历史及保存部署路径", "CPU验证配置及模型/数据schema，复核独立wall10实际差异", "生成完整差异清单、重构取舍及工程交接"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/physhsi_full_audit_20261023/check_sources.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/physhsi_full_audit_20261023/check_data.py"}]
stop_conditions: ["源码身份在审计期间变化则重新核验相关结论", "冻结检查失败最多两次原范围修复并保留回执", "无法读取来源时明确待核验，不补造值"]
safeguards: ["全部CPU只读；测试仅写本任务docs", "保留既有wall10未提交实现和其他工作区改动", "配置声明与实际调用区分，数据/模型身份和单位/坐标系逐项记录"]
expert_required: true
device_actions: []
real_device_authorized: false
expert_brief: {"affected_call_path": ["PhysHSI G1 carrybox config/env -> motionlib -> explicit PD/PhysX -> post-step reward/reset -> HIMPPO/AMP", "wall5 config -> PhysHSI reset/delay helper -> implicit actuator -> inherited X2/grasp rewards -> independent PPO/AMP", "Independent wall10 config -> explicit PD -> source-style regularization/joint PPO/AMP; inspect as separate variant"], "critical_interfaces": ["29 named joints; 5 ms physics/20 ms policy; source xyzw and Lab wxyz; link-origin positions versus COM velocities", "60D AMP order/frame; actor depth/proprio only; privileged critic/pose/AMP training-only", "Default/RSI reference selection, final joint pose, foot clearance, paired box/platform, terminal data before reset"], "invariants": ["Keep original files/weights, checkpoint schemas and unrelated football changes", "Do not equate nominal Kp/Kd with implicit/explicit control equivalence", "Do not count held-box RSI as a successful ground pickup; separate effective terms from inactive declarations"], "smallest_change_locus": ["Read-only audit artifacts and project index entries; no production change"], "mandatory_safeguards": ["全部CPU只读；测试仅写本任务docs", "保留既有wall10未提交实现和其他工作区改动", "配置声明与实际调用区分，数据/模型身份和单位/坐标系逐项记录"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python docs/carrybox/physhsi_full_audit_20261023/check_sources.py", "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/physhsi_full_audit_20261023/check_data.py"], "blockers": ["源码身份在审计期间变化则重新核验相关结论", "冻结检查失败最多两次原范围修复并保留回执", "无法读取来源时明确待核验，不补造值"]}
---

以当前wall5 rev28为主，逐项对照本地PhysHSI G1 carrybox实际生效训练实现、resources资产/数据/训练checkpoint；补充独立wall10现状。只读核验并提供可追溯差异表和重构边界，不修改训练实现或操作正式进程。
