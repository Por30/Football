---
task_id: "AGILE-V2-SPEED-ONLY-20260925"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v2.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v2_env_cfg.py", "tests/test_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.sh", "docs/agilekickball_v2", "README.md", "agent/plan/agilekickball-v2-speed-only.md", "agent/task/agilekickball-v2-speed-only.md", "agent/report/agilekickball-v2-speed-only.md", "agent/handoff/agilekickball-v2-speed-only.md"]
development_modes: ["ML_TRAINING", "STATE_MACHINE"]
original_request: "看最新训练记录mean episode length上不去的原因；排查后修改v2，v1能够连续踢球为什么v2加课程不行"
forbidden_scope: ["修改v0/v1与共享奖励或网络PPO", "自动启动长训练或修改现有checkpoint", "声称短测证明高速策略学成"]
steps: ["比对最新run版本和v1训练窗口", "归档旧v2并恢复继承v1恢复奖励与采样", "只实施连续恢复门控的速度扩展和schema5", "执行回归与真实CPU PPO/连续发球/高速可见性短测", "生成诊断、设计、报告和从零训练命令"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v2.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v2.sh"}]
stop_conditions: ["范围扩大或需要长训练", "冻结测试两次范围内修复后仍失败", "实机操作"]
safeguards: ["保持v1相同RNG采样顺序与reset/tick/serve/balanced", "日志区分恢复占比和kick代理，均非严格成功率", "显式版本和schema，旧checkpoint在policyload之前拒绝", "play冻结与速度override；resume不复用旧环境计数器窗口", "保留有限值、5秒恢复超时和终止优先级；不改失败判据", "same-step sync idempotent; previous rate integrates next interval; no retroactive unlock progress", "insufficient window samples sets future rate zero", "marginal shares are not joint success; gate clamp but retain raw shares and counts", "schema5 finite/bounds/boolean validation before weights; reject missing/old course", "resume rebases control and counts, discards partial window", "metrics must not sync and change v1 schedule", "short tests do not prove learning; schema3 logs not evidence against untrained schema4"]
expert_required: true
device_actions: []
real_device_authorized: false
expert_brief: {"affected_call_path": ["startup -> inherited v1 round state -> reset-time curriculum -> runner checkpoint"], "critical_interfaces": ["V1 constructor virtual sync avoided", "runner sets train/play mode after course load", "serve samples distance before speed"], "invariants": ["v1 physical methods/config/RNG unchanged", "monotonic upper<=6", "freeze and override"], "smallest_change_locus": ["v2 state and cfg", "v2 tests and smoke"], "mandatory_safeguards": ["same-step sync idempotent; previous rate integrates next interval; no retroactive unlock progress", "insufficient window samples sets future rate zero", "marginal shares are not joint success; gate clamp but retain raw shares and counts", "schema5 finite/bounds/boolean validation before weights; reject missing/old course", "resume rebases control and counts, discards partial window", "metrics must not sync and change v1 schedule", "short tests do not prove learning; schema3 logs not evidence against untrained schema4"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v2.py", "bash scripts/rsl_rl/smoke_agilekickball_v2.sh"], "blockers": []}
---

恢复v1已验证的连续球行为；只有速度课程允许改变。旧schema3最新运行未加载schema4修正，不能混淆版本。先按v1曝光课程学基础，再按近期恢复发球表现解锁加速，能力不足暂停扩展。