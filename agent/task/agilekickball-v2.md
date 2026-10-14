---
task_id: "AGILE-V2-RECOVERY-20260924"
language: "zh-CN"
axes: ["L", "D", "C"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["ML_TRAINING", "STATE_MACHINE", "SIMULATOR_EXTENSION"]
original_request: "新建v2，让速度课程更容易推进，至少学会5以上球速；设定合理课程和恢复机制，构思论文候选创新后加到v2，用稳定性衡量踢球任务。"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v2.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v2_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "tests/test_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.sh", "docs/agilekickball_v2", "README.md", "agent/plan/agilekickball-v2.md", "agent/task/agilekickball-v2.md", "agent/report/agilekickball-v2.md", "agent/handoff/agilekickball-v2.md"]
forbidden_scope: ["更改v0/v1行为", "网络或奖励重构", "长训练或实机", "宣称已验证创新/高速能力", "自动推送GitHub"]
steps: ["冻结候选机制和验证口径", "实现独立v2恢复状态机和速度采样", "注册任务及checkpoint接口", "实现回合统计和聚焦测试", "运行CPU集成冒烟并生成报告"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v2.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v2.sh"}]
stop_conditions: ["需要扩大允许路径", "两次范围内修复后冻结测试仍失败", "涉及实机或长训练"]
safeguards: ["仅v2，v0/v1行为不变，保持观察网络奖励", "球结束冷却20步+当下稳定+5s硬截止+无reset才发", "每球success/failure/censored唯一结算和计数守恒", "冻结strike方向并在teleport前判回程；全闭合球为CDF分母", "发球起累计扰动峰值；稳定时间.2-.4s、身体漂移<.6m；失衡清驻留不清时钟", "课程与评估统计隔离；play冻结课程EMA；checkpoint严格schema/config/finite校验", "控制步上限按120k/.8,360k/2,720k/5,840k/6，挑战概率>=.25", "真实CPU冒烟与构造状态分开报告；不启动长训练/实机"]
expert_required: true
expert_brief: {"affected_call_path": ["tick -> recovery -> parent ball tick -> settle -> serve -> statistics", "runner -> validate before policy load -> restore/freeze course"], "critical_interfaces": ["termination先于reward；父tick动态serve/reset；v1构造虚sync"], "invariants": ["仅v2，v0/v1行为不变，保持观察网络奖励", "球结束冷却20步+当下稳定+5s硬截止+无reset才发", "每球success/failure/censored唯一结算和计数守恒", "冻结strike方向并在teleport前判回程；全闭合球为CDF分母", "发球起累计扰动峰值；稳定时间.2-.4s、身体漂移<.6m；失衡清驻留不清时钟", "课程与评估统计隔离；play冻结课程EMA；checkpoint严格schema/config/finite校验", "控制步上限按120k/.8,360k/2,720k/5,840k/6，挑战概率>=.25", "真实CPU冒烟与构造状态分开报告；不启动长训练/实机"], "smallest_change_locus": ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v2.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v2_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py"], "mandatory_safeguards": ["仅v2，v0/v1行为不变，保持观察网络奖励", "球结束冷却20步+当下稳定+5s硬截止+无reset才发", "每球success/failure/censored唯一结算和计数守恒", "冻结strike方向并在teleport前判回程；全闭合球为CDF分母", "发球起累计扰动峰值；稳定时间.2-.4s、身体漂移<.6m；失衡清驻留不清时钟", "课程与评估统计隔离；play冻结课程EMA；checkpoint严格schema/config/finite校验", "控制步上限按120k/.8,360k/2,720k/5,840k/6，挑战概率>=.25", "真实CPU冒烟与构造状态分开报告；不启动长训练/实机"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v2.py", "bash scripts/rsl_rl/smoke_agilekickball_v2.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

# AgileKickball v2

实现速度条件恢复包络候选：探索上限保证高速训练机会，已结算联合成功影响练习/挑战采样；恢复在球飞出时并行完成。冻结任务用独立状态机回归及真实CPU仿真冒烟验收，科研假设另见 docs/agilekickball_v2/research_card.json。
