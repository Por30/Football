---
task_id: "carrybox-wall4-render6s"
language: "zh-CN"
axes: ["P", "A"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/carrybox_camera.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/benchmark_carrybox_render.py", "scripts/rsl_rl/benchmark_carrybox_render.sh", "tests/test_carrybox_camera.py", "docs/carrybox/render6s_20261014", "docs/carrybox/performance_20261014", "projects/README.md", "projects/findbox/README.md", "README.md", "agent", "logs/rsl_rl/g1_carrybox_depth/walled4"]
original_request: "正常一轮应该是在6s以内的"
forbidden_scope: ["改足球/系统库/原始数据/动作奖励", "减少4096/24步/PPOepochs/相机频率来满足6秒", "使用验证模型作为正式恢复模型"]
development_modes: ["SENSOR_DRIVER", "ML_TRAINING", "SYSTEM_TUNING"]
steps: ["记录运行状态与耗时并停训", "独立4环境比较FSD与深度渲染设置及geometry", "4096分组profile和完整PPO/AMP恢复验收", "仅应用等价通过且有收益的配置", "恢复正式训练并明确6秒达标与否"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}, {"command": "bash scripts/rsl_rl/benchmark_carrybox_render.sh"}]
safeguards: ["保持4096x24与完整PPO/AMP更新、48x27/50Hz及深度噪声/延迟配对，不减少控制/奖励/任务规模", "FSD在stage加载前由本任务独立进程启用，记录实际设置和加载扩展；不改系统或足球", "保留renderer/hydra waitIdle同步及rerender_on_reset，4环境运动/部分reset首帧/安装扰动/遮挡与独立PhysX乘USD局部位姿验证", "记录真实线程数和Carb配置，profile与非profile计时分离；6s以完整PPO迭代实测", "只恢复正式checkpoint，保留全部历史/失败记录"]
stop_conditions: ["任一深度/位姿/首帧/碰撞/恢复不一致则撤回该候选", "冻结测试失败最多两次原范围生产修复；若最优等价候选仍不达6秒，报告实际差距，不降低语义冒充完成"]
expert_required: true
expert_brief: {"affected_call_path": ["AppLauncher -> 4.5 headless kit -> render presets -> RTX tiled camera + walled camera pose"], "critical_interfaces": ["FSD两项stage首次加载锁定；实际AA设置需dump", "Fabric局部camera/robot reset同步；默认balanced覆盖基础kit"], "invariants": ["保持4096x24与完整PPO/AMP更新、48x27/50Hz及深度噪声/延迟配对，不减少控制/奖励/任务规模"], "smallest_change_locus": ["walled渲染配方与启动参数；必要时只在walled相机缓存静态安装且setter明确失效"], "mandatory_safeguards": ["保持4096x24与完整PPO/AMP更新、48x27/50Hz及深度噪声/延迟配对，不减少控制/奖励/任务规模", "FSD在stage加载前由本任务独立进程启用，记录实际设置和加载扩展；不改系统或足球", "保留renderer/hydra waitIdle同步及rerender_on_reset，4环境运动/部分reset首帧/安装扰动/遮挡与独立PhysX乘USD局部位姿验证", "记录真实线程数和Carb配置，profile与非profile计时分离；6s以完整PPO迭代实测", "只恢复正式checkpoint，保留全部历史/失败记录"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "bash scripts/rsl_rl/benchmark_carrybox_render.sh"], "blockers": ["任一深度/位姿/首帧/碰撞/恢复不一致则撤回该候选", "冻结测试失败最多两次原范围生产修复；若最优等价候选仍不达6秒，报告实际差距，不降低语义冒充完成"]}
device_actions: []
real_device_authorized: false
---

目标为4096环境×24控制步的完整训练迭代<=6秒。前版约21秒，继续按真实profile优化渲染/场景更新；不承诺未验证倍率。用户被可选询问6秒参考配置，工作不依赖答复。复用wall4_perf_review单个只读专家，4.5 FSD支持已核对本机头文件/官方测试。
