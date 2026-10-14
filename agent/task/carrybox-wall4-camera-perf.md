---
task_id: "carrybox-wall4-camera-perf"
language: "zh-CN"
axes: ["P", "A"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_camera.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "scripts/rsl_rl/benchmark_carrybox_camera.py", "scripts/rsl_rl/benchmark_carrybox_camera.sh", "tests/test_carrybox_camera.py", "docs/carrybox/performance_20261014", "docs/carrybox/scale4096_20261014", "projects/README.md", "projects/findbox/README.md", "README.md", "agent", "logs/rsl_rl/g1_carrybox_depth/walled4"]
original_request: "训练间间很长 你看能不能修改一下"
forbidden_scope: ["改足球、共享系统库、奖励控制/样本规模或相机语义", "删除历史数据模型或以验证checkpoint冒充正式产物"]
development_modes: ["SENSOR_DRIVER", "ML_TRAINING"]
steps: ["记录原4096耗时并停训保留checkpoint", "实现walled专属批量相机位姿候选", "4环境运动reset遮挡标签等价验收", "4096 profile及PPO/AMP保存恢复短测", "收益成立后恢复正式训练并记录限制"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}, {"command": "bash scripts/rsl_rl/benchmark_carrybox_camera.sh"}]
stop_conditions: ["位姿/遮挡/标签或恢复不一致则撤回候选，不降低传感频率或环境数", "冻结测试失败最多两次原范围修复，4096收益必须实测"]
safeguards: ["保持4096、RTX遮挡、48x27和50Hz、噪声/延迟/冻结、actor/critic边界及奖励控制PPO不变", "只由walled选择专属camera子类，不改足球/基线/System", "独立PhysX torso乘USD局部相机位姿对照，运动及[3,1]部分reset后验证，不仅比较共享Fabric缓存的getter", "初始化与稳态计时分开，CUDA同步；验证遮挡、标签配对及checkpoint恢复", "保存历史模型；优化不通过不用于正式训练"]
expert_required: true
expert_brief: {"affected_call_path": ["walled3/4 camera._update_buffers_impl/reset/_create_buffers -> _update_poses -> get_world_poses -> box_pose_target/paired buffer"], "critical_interfaces": ["Fabric全量无indices获取避免int64/Warp.view；wxyz/OpenGL转world，subset写入", "首次Fabric查询新增world attrs，需独立几何参考"], "invariants": ["4096环境与任务/传感训练配方不变"], "smallest_change_locus": ["walled专属TiledCamera._update_poses批量Fabric查询及cfg.class_type"], "mandatory_safeguards": ["保持4096、RTX遮挡、48x27和50Hz、噪声/延迟/冻结、actor/critic边界及奖励控制PPO不变", "只由walled选择专属camera子类，不改足球/基线/System", "独立PhysX torso乘USD局部相机位姿对照，运动及[3,1]部分reset后验证，不仅比较共享Fabric缓存的getter", "初始化与稳态计时分开，CUDA同步；验证遮挡、标签配对及checkpoint恢复", "保存历史模型；优化不通过不用于正式训练"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "bash scripts/rsl_rl/benchmark_carrybox_camera.sh"], "blockers": ["位姿/遮挡/标签或恢复不一致则撤回候选，不降低传感频率或环境数", "冻结测试失败最多两次原范围修复，4096收益必须实测"]}
device_actions: []
real_device_authorized: false
---

用户要求缩短训练耗时。4096正式日志采样约24秒、更新约1.5秒；相机当前逐个CPU位姿查询。只验证/优化读取后端，保留语义，不减少任务规模。训练已停23轮，最近保存model_0.pt保留；验证通过后从该正式checkpoint恢复，验证模型不进入正式训练。

只读组合专家wall4_perf_review已完成审查；关键风险是Fabric初始化后相机子变换同步，必须真实仿真证明。
