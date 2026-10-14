---
task_id: "AGILE-V2-STABILITY-FIX-20260924"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v2.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v2_env_cfg.py", "tests/test_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.sh", "docs/agilekickball_v2", "README.md", "agent/plan/agilekickball-v2-stability-fix.md", "agent/task/agilekickball-v2-stability-fix.md", "agent/report/agilekickball-v2-stability-fix.md", "agent/handoff/agilekickball-v2-stability-fix.md"]
development_modes: ["ML_TRAINING", "STATE_MACHINE"]
original_request: "停止后台训练 然后给我启动修改后的v2下命令；训练的命令呢"
forbidden_scope: ["修改v0/v1共享行为或网络PPO", "自动重新启动长训练", "声称短测证明高速学习成功"]
steps: ["停止旧后台训练并归档旧契约", "修正发球距离和恢复门控", "补严格即时/联合成功/失败奖励并提升schema", "执行状态机回归及真实CPU奖励排序/PPO/相机检查", "给从零启动命令并完成报告"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v2.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v2.sh"}]
stop_conditions: ["需要扩大代码范围", "两次范围内修复后冻结测试仍失败", "需要长训练或实机"]
safeguards: ["单次serve预采speed并缓存，parent距离tensor按相同ids，finally恢复缓存/范围，sample统计只一次", "jointpulse有效tick开始清，settle置位后same-tick serve不清，终止优先于发球", "失败奖励读terminated排除纯time_out，权重积分dt=.02后为2/8/-8 before AMP", "严格足部代理门控即时和return奖励；被动反弹不免miss，不因新球teleport获得回程", "恢复恢复v1 inactive stable .3s/wait .4..5s，active outbound不受5秒限制", "v0/v1观察网络PPO不变；旧schema/config在policyload前拒绝；play冻结与override保持", "CPU短测不证明从零训练已稳定/学会5以上；不给旧坏策略续训；不自动启动长训练"]
expert_required: true
expert_brief: {"affected_call_path": ["termination compute -> state tick -> settle/serve -> rewards -> reset -> runner"], "critical_interfaces": ["parent先距离后速度，预采缓存桥接", "奖励先于reset；runner已有validate钩子"], "invariants": ["serve账本守恒", "control clock独立环境数", "v0/v1行为保留"], "smallest_change_locus": ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v2.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v2_env_cfg.py", "tests/test_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.sh"], "mandatory_safeguards": ["单次serve预采speed并缓存，parent距离tensor按相同ids，finally恢复缓存/范围，sample统计只一次", "jointpulse有效tick开始清，settle置位后same-tick serve不清，终止优先于发球", "失败奖励读terminated排除纯time_out，权重积分dt=.02后为2/8/-8 before AMP", "严格足部代理门控即时和return奖励；被动反弹不免miss，不因新球teleport获得回程", "恢复恢复v1 inactive stable .3s/wait .4..5s，active outbound不受5秒限制", "v0/v1观察网络PPO不变；旧schema/config在policyload前拒绝；play冻结与override保持", "CPU短测不证明从零训练已稳定/学会5以上；不给旧坏策略续训；不自动启动长训练"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v2.py", "bash scripts/rsl_rl/smoke_agilekickball_v2.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

# v2稳定性修正

基于9条件CPU回放与训练日志修正早期距离、固定恢复和奖励错配；已停止旧进程，保留6m/s覆盖，不自动启动用户长训练。旧契约与结果在stability_fix_20260924/before归档。
