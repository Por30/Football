---
task_id: "ENG-AGILE-V1-SIMPLE-SPEED-20260922"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["ML_TRAINING", "STATE_MACHINE"]
original_request: "重新在v0 基础上修改v1 让课程的设计逻辑更理理 我只是想逐步提高来球的度度"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v1.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v1_env_cfg.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "tests/test_agilekickball_v1.py", "tests/test_play_ballspeed.py", "scripts/rsl_rl/smoke_agilekickball_v1.py", "scripts/rsl_rl/smoke_agilekickball_v1.sh", "docs/agilekickball_v1", "agent"]
forbidden_scope: ["修改v0源文件/奖励/网络/PPO/深度监督", "长训练、终止用户进程、真实硬件"]
steps: ["归档strict旧实现与验收，重建v1薄子类", "新课程key与冻结加载，保留play override", "有界CPU与真实仿真验证", "写说明和报告并校验"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v1.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_play_ballspeed.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v1.sh"}]
stop_conditions: ["范围外修改", "同一验证失败修复超过两轮"]
safeguards: ["这是有证据支持的恢复判据调整，不等于已证明所有恢复失败都来自关节 RMS；报告中保留旧 stochastic 诊断与修改后实际门控数据。", "balanced 不能通过修改 robot.data.joint_vel 再调用父类实现；直接在 v1 覆写对应布尔表达式，保留所有其他阈值。", "测试应构造高关节 RMS、其他条件满足时 v1 可恢复而 v0 不可恢复；逐项破坏保留的物理条件时 v1 仍不得发球。", "曝光值及 checkpoint 参数校验 finite、非负；拒绝 NaN/Inf、负值及错误 schema/config，避免错误速度范围进入物理仿真。", "旧 strict checkpoint 不允许静默迁移；若另有权重 warm start，应明确丢弃其课程状态。合法 v0 checkpoint 可按已保存曝光继续前段课程。", "冻结评测需固定课程所用曝光快照，不能仅设置 curriculum_training=False 却继续从增长的 exposure_steps 重算课程；保存冻结状态时也应采用同一快照。", "--ballspeed 的实际采样与日志保持一致；课程同步不得覆盖该显式评测范围，恢复训练时不要持久化临时评测 override。", "CPU 验证 0、60000、240000 前后、480000 及超出上限的数值边界；验证无来球时不推进、变更 num_envs 后按平均曝光恢复。", "真实 smoke 使用正常动作与物理状态验证首球、恢复后重发、checkpoint/play freeze 和速度 override；短跑不证明在 5 m/s 下已学会踢球。"]
expert_required: true
expert_brief: {"affected_call_path": ["v1配置→v0 reset/tick/_serve→mean incoming exposure→两段速度与原距离课程→均匀发球", "runner新key/schema→play冻结→ballspeed→reset"], "critical_interfaces": ["课程保持reset-time更新频率；无_serve覆写", "v0 exposure_steps=offset+incoming_steps.mean，活跃向内且未终止才增加", "旧strict key优先拒绝；新key agile_speed_curriculum；v0 key用于合法曝光迁移"], "invariants": ["前240000曝光上限0.8→2，后240000曝光2→5，下限0.4", "距离v0前60000曝光(0.5,0.7)→(1.3,2)", "v0文件/奖励/观测/网络/PPO不变；v1仅移除joint RMS门控", "加载曝光offset后清零当前计数；play使用冻结快照"], "smallest_change_locus": ["v1薄子类balanced/课程存取", "v1配置/runner新key", "测试smoke文档"], "mandatory_safeguards": ["这是有证据支持的恢复判据调整，不等于已证明所有恢复失败都来自关节 RMS；报告中保留旧 stochastic 诊断与修改后实际门控数据。", "balanced 不能通过修改 robot.data.joint_vel 再调用父类实现；直接在 v1 覆写对应布尔表达式，保留所有其他阈值。", "测试应构造高关节 RMS、其他条件满足时 v1 可恢复而 v0 不可恢复；逐项破坏保留的物理条件时 v1 仍不得发球。", "曝光值及 checkpoint 参数校验 finite、非负；拒绝 NaN/Inf、负值及错误 schema/config，避免错误速度范围进入物理仿真。", "旧 strict checkpoint 不允许静默迁移；若另有权重 warm start，应明确丢弃其课程状态。合法 v0 checkpoint 可按已保存曝光继续前段课程。", "冻结评测需固定课程所用曝光快照，不能仅设置 curriculum_training=False 却继续从增长的 exposure_steps 重算课程；保存冻结状态时也应采用同一快照。", "--ballspeed 的实际采样与日志保持一致；课程同步不得覆盖该显式评测范围，恢复训练时不要持久化临时评测 override。", "CPU 验证 0、60000、240000 前后、480000 及超出上限的数值边界；验证无来球时不推进、变更 num_envs 后按平均曝光恢复。", "真实 smoke 使用正常动作与物理状态验证首球、恢复后重发、checkpoint/play freeze 和速度 override；短跑不证明在 5 m/s 下已学会踢球。"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v1.py", "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_play_ballspeed.py", "bash scripts/rsl_rl/smoke_agilekickball_v1.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

用户明确取消复杂成功晋级要求。本次替换对应strict测试合同，旧源码/测试/smoke归档供审计，不把旧strict断言改成恒真。所有继承的v0/学习回归仍执行。最终交付从头训练命令4096环境/50000轮，不含resume。
