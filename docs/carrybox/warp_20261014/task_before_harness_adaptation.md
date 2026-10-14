---
task_id: "carrybox-wall4-warp"
language: "zh-CN"
axes: ["P", "A"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_raycast.py", "source/perceptual_ball/perceptual_ball/carrybox_warp_camera.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/benchmark_carrybox_warp.py", "scripts/rsl_rl/benchmark_carrybox_warp.sh", "tests/test_carrybox_raycast.py", "docs/carrybox/warp_20261014", "docs/carrybox/render6s_20261014/launch.json", "README.md", "projects/README.md", "projects/findbox/README.md", "agent", "logs/rsl_rl/g1_carrybox_depth/walled4"]
artifact: "TASK"
status: "FROZEN"
original_request: "继续迁移 确保深度训练时间正常后在启动式式训练 同时也可以看看本地kicnball任务怎怎么训练的 那个训练间间也是正常的"
development_modes: ["SENSOR_DRIVER", "SIMULATOR_EXTENSION", "ML_TRAINING"]
forbidden_scope: ["改足球、系统依赖、原始数据、奖励动作/特权策略", "未达正确性和<=6秒先启动正式训练", "降低环境数/rollout/epoch/相机频率冒充提速"]
steps: ["停训并保存状态，审查football与sensor接口", "实现共享静态BVH+动态局部ray求交、配置与契约", "CPU及4环境RTX/遮挡/reset对照", "4096全更新8轮与恢复计时", "仅验收通过显式迁移正式权重并验证训练、更新文档"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}, {"command": "bash scripts/rsl_rl/benchmark_carrybox_warp.sh"}]
safeguards: ["4096x24、PPO/AMP完整更新、48x27/50Hz、原始数据与奖励不变", "所有有效视觉mesh含机身、自遮挡及箱/墙/柱/平台/地面，物理link坐标和像素中心/光轴near-far保持", "terminal前reset后深度/标签配对、安装扰动、部分reset和运动kinematics验证", "旧RTX模型契约默认拒绝，正式如迁移仅显式weights warm-start；docs模型不能正式使用", "完整正确性及热身后所有完整迭代<=6s才正式启动，否则保持停止"]
stop_conditions: ["任何覆盖/帧/坐标/恢复验收失败不得正式启动", "冻结失败最多两次原范围生产修复；耗时超6s保持停止并记录未达标"]
expert_required: true
expert_brief: {"affected_call_path": ["walled scene SensorBase -> CameraData -> captured_pair -> PPO/AMP；football仅只读对照"], "critical_interfaces": ["内建RayCaster只支持单static，新增任务内multi-dynamic Warp sensor", "PhysX link frame而非COM；动态rigid变换，视觉scale bake；CameraData兼容"], "invariants": ["4096x24、PPO/AMP完整更新、48x27/50Hz、原始数据与奖励不变", "所有有效视觉mesh含机身、自遮挡及箱/墙/柱/平台/地面，物理link坐标和像素中心/光轴near-far保持", "terminal前reset后深度/标签配对、安装扰动、部分reset和运动kinematics验证", "旧RTX模型契约默认拒绝，正式如迁移仅显式weights warm-start；docs模型不能正式使用", "完整正确性及热身后所有完整迭代<=6s才正式启动，否则保持停止"], "smallest_change_locus": ["任务专属Warp mesh kernel/sensor、walled配置和reset同步；保留RTX选项作对照"], "mandatory_safeguards": ["4096x24、PPO/AMP完整更新、48x27/50Hz、原始数据与奖励不变", "所有有效视觉mesh含机身、自遮挡及箱/墙/柱/平台/地面，物理link坐标和像素中心/光轴near-far保持", "terminal前reset后深度/标签配对、安装扰动、部分reset和运动kinematics验证", "旧RTX模型契约默认拒绝，正式如迁移仅显式weights warm-start；docs模型不能正式使用", "完整正确性及热身后所有完整迭代<=6s才正式启动，否则保持停止"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "bash scripts/rsl_rl/benchmark_carrybox_warp.sh"], "blockers": ["RTX/Warp深度/遮挡/near/partialreset不一致不得正式启动", "FSD 4.5禁用physics，不采用"]}
device_actions: []
real_device_authorized: false
---

用户要求迁移动态Warp深度并先验收速度再开正式训练。使用wall4_perf_review唯一只读专家。足球真实日志约2.47秒但仅球解析深度，不能移植其遮挡简化。当前Wall4已发SIGINT且进程退出，旧正式模型保留。新契约区分RTX与Warp，warm-start不继承旧AMP optimizer。
