---
task_id: "carrybox-wall5-semantic-20261020"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_reward_geometry.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "source/perceptual_ball/perceptual_ball/carrybox_walled.py", "tests/test_carrybox_reward_geometry.py", "tests/test_carrybox_reset_bug.py", "tests/test_carrybox_distance3d.py", "docs/carrybox/wall5_semantic_20261020", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-semantic-20261020.md", "agent/task/carrybox-wall5-semantic-20261020.md", "agent/report/carrybox-wall5-semantic-20261020.md", "agent/handoff/carrybox-wall5-semantic-20261020.md"]
original_request: "G1 奖励与阈值的语义对齐 先做个个然后重新启训练"
development_modes: ["SIMULATION", "ML_TRAINING"]
forbidden_scope: ["不修改观测/网络/AMP/PPO/RSI/相机/资产/数据，不复制X2旧bug", "不得改wall3/4或足球默认行为，不覆盖已有记录或恢复旧训练", "不把FK或启动短测当作稳定/抱箱成功证明"]
steps: ["按片段等权测G1参考姿态几何，统一阈值/指数尺度并检查有效蹲姿终止边界", "实现wall5集中几何配置及pelvis参考，取消独立稳定项和walk乘法，更新revision19契约", "执行CPU门控边界/默认隔离与4环境更新、保存恢复短测", "仅在前述检查通过后核实旧训练进程并停止，启动4096 fresh正式训练", "核验新run进度/耗时/优化器/契约，更新项目状态和交接"]
tests: [{"command": "bash docs/carrybox/wall5_semantic_20261020/check.sh"}, {"command": "bash docs/carrybox/wall5_semantic_20261020/smoke.sh"}, {"command": "bash docs/carrybox/wall5_semantic_20261020/verify.sh"}]
stop_conditions: ["前两项检查不通过不停止旧训练、不启动正式run", "训练身份不匹配、资源不足、NaN/OOM/契约错误立即停止本次启动并报告", "最多两次范围内测试修复，不放宽验收断言", "具体阈值需实际标定，不用附件估值代替"]
safeguards: ["测量64帧/行走片段，gravity XY<0.2，11片段等权中位数；持箱32帧；同批读取足底/骨盆/头，报告分母和分位数", "保持X2站立水平接近半径sqrt(0.7²-(0.669-0.125)²)，高度指数按尺度反比调整", "standup/search使用pelvis；head COM/world-ground；保留Box过滤手接触、原比较符号和RewardManager单次weight*dt", "仅wall5配置覆盖；actor372+depth/critic108/AMP600、RSI80/20、roll0.5、失败罚和增量推扰课程不变", "strict load拒绝rev18；正式无resume/warm-start，4096、seed42、40000轮；最后10轮≤6s", "verify.sh只在check/smoke成功凭据和源码hash均一致时执行已授权重启；只停止匹配完整命令的旧PID", "等权实际FK几何/分母；指数尺度；蹲姿终止；不得称动态稳定"]
expert_required: true
expert_brief: {"affected_call_path": ["wall5 config→walk/reward_terms/search/held/fallen→RewardManager→日志/contract"], "critical_interfaces": ["XYZ距离；world-ground高度；pelvis standup/search；保留手对Box过滤"], "invariants": ["旧任务默认、观测/PPO/AMP/RSI和单次weight*dt不变，严格比较符不变"], "smallest_change_locus": ["集中几何配置+可选共享参数，移除稳定注册/乘法/日志，revision19"], "mandatory_safeguards": ["等权实际FK几何/分母；指数尺度；蹲姿终止；不得称动态稳定"], "minimal_tests": ["bash docs/carrybox/wall5_semantic_20261020/check.sh", "bash docs/carrybox/wall5_semantic_20261020/smoke.sh", "bash docs/carrybox/wall5_semantic_20261020/verify.sh"], "blockers": ["具体阈值需实际标定，不用附件估值代替"]}
device_actions: []
real_device_authorized: false
---

冻结范围是G1奖励语义适配和用户已授权的正式从零重启。verify命令含检查通过后的旧进程停止、新训练启动与只读验收；不会自动恢复旧模型。几何探针属于参考姿态FK，不提供接触动态或收敛证据。

工件格式校正：专家字段转换为校验器要求的列表，保留同一范围、三条冻结命令、边界与要求。标定前置条件已经由geometry.json满足。
