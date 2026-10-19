---
task_id: "carrybox-wall5-asymmetric-20261019"
language: "zh-CN"
axes: ["L", "A"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "仅critic改用本体＋机体线速度＋箱子位姿/尺寸真值，独立MLP；actor保持深度＋本体，停止当前wall5并4096环境从零重启。"
development_modes: ["ML_TRAINING"]
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "tests/test_carrybox_asymmetric.py", "docs/carrybox/wall5_asymmetric_20261019", "projects/README.md", "projects/findbox/README.md", "AGENTS.md", "logs/rsl_rl/g1_carrybox_depth/walled5", "agent/plan/carrybox-wall5-asymmetric-20261019.md", "agent/task/carrybox-wall5-asymmetric-20261019.md", "agent/report/carrybox-wall5-asymmetric-20261019.md", "agent/handoff/carrybox-wall5-asymmetric-20261019.md"]
forbidden_scope: ["修改actor输入/网络、深度、AMP、奖励、RSI、碰撞或football/wall3/wall4", "删除旧数据/模型/日志或恢复旧checkpoint替代fresh", "真实硬件动作"]
steps: ["核对在训身份，明确wall5训练专用critic输入和契约", "实现108维当前本体/线速度/箱子局部xyz+rot6/尺寸及独立MLP，修正终止前critic快照", "CPU信息隔离/梯度/超时/导出/恢复回归与4环境真实更新验收", "停止旧wall5保留产物，以4096环境fresh正式启动并核验连续迭代、checkpoint与耗时", "更新项目入口、约定的wall5例外、四工件及证据"]
tests: [{"command": "bash docs/carrybox/wall5_asymmetric_20261019/check.sh"}, {"command": "bash docs/carrybox/wall5_asymmetric_20261019/smoke.sh"}, {"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_asymmetric_20261019/verify_launch.py"}]
stop_conditions: ["两次范围内修复后测试仍失败", "输入泄漏或非有限输出", "正式训练错误/资源不足则不重复启动"]
safeguards: ["actor只读372维4帧本体和4x27x48深度，辅助监督不变", "critic108维独立MLP不经过CNN；相对位姿以pelvis link坐标系表示，尺寸为箱子局部完整边长米制", "pre-reset终止critic用于timeout bootstrap，其他环境历史不污染", "迁移revision14严格拒绝旧完整resume，原run/model保留", "同用户已授权4096 fresh训练；操作前核对PID命令，非目标进程不操作", "不改变AMP数据/Normalizer/PPO超参/相机/部署actor接口", "停止前再次核对PID3812053命令与启动身份；只停止目标，确认退出及GPU资源释放，保留原run/checkpoint/log。", "独立4096 fresh正式run，无resume/warm-start/验证模型加载；启动失败先诊断修复，不盲目重复启动。", "正式核验命令/配置/连续迭代/耗时和schema2/revision14/critic108/有限参数/优化器及Normalizer初始计数。", "仅wall5为特权critic例外；短测和正式启动不能推断收敛。"]
expert_required: true
expert_brief: {"affected_call_path": ["Wall5ObservationsCfg→critic_state→独立critic→PPO rollout/returns/快路", "Wall5._reset_idx→pre-reset terminal→timeout bootstrap", "wall5 runner/checkpoint和actor-only export"], "critical_interfaces": ["critic108:当前本体93+pelvis link线速度3+箱xyz3/rot6/size3", "actor372+depth[4,27,48]；critic MLP108/512/256/256/1", "terminal env_ids顺序对应，gamma*V只加一次"], "invariants": ["actor/export不读特权；value gradient不进入CNN/actor/pose", "actor与pose共用一次CNN；其他任务/AMP/奖励/RSI/PPO不变", "m、m/s和pelvis link坐标一致"], "smallest_change_locus": ["三个wall5生产文件；共享train/play/export不改"], "mandatory_safeguards": ["停止前再次核对PID3812053命令与启动身份；只停止目标，确认退出及GPU资源释放，保留原run/checkpoint/log。", "独立4096 fresh正式run，无resume/warm-start/验证模型加载；启动失败先诊断修复，不盲目重复启动。", "正式核验命令/配置/连续迭代/耗时和schema2/revision14/critic108/有限参数/优化器及Normalizer初始计数。", "仅wall5为特权critic例外；短测和正式启动不能推断收敛。"], "minimal_tests": ["bash docs/carrybox/wall5_asymmetric_20261019/check.sh", "bash docs/carrybox/wall5_asymmetric_20261019/smoke.sh", "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_asymmetric_20261019/verify_launch.py"], "blockers": []}
device_actions: []
real_device_authorized: false
---


用户本次明确授权仅wall5 critic使用特权状态，覆盖旧无特权critic约定；其余CarryBox与football保持原接口。
专家原文见docs/carrybox/wall5_asymmetric_20261019/expert_review.md；这里只修正brief为校验器要求的内嵌七字段，原三条冻结测试命令和实现范围不变。
