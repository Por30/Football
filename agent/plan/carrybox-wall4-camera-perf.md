---
task_id: "carrybox-wall4-camera-perf"
language: "zh-CN"
axes: ["P", "A"]
risk_tier: "T2"
artifact: "PLAN"
status: "DONE"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_camera.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "scripts/rsl_rl/benchmark_carrybox_camera.py", "scripts/rsl_rl/benchmark_carrybox_camera.sh", "tests/test_carrybox_camera.py", "docs/carrybox/performance_20261014", "docs/carrybox/scale4096_20261014", "projects/README.md", "projects/findbox/README.md", "README.md", "agent", "logs/rsl_rl/g1_carrybox_depth/walled4"]
---

用户要求缩短训练耗时。4096正式日志采样约24秒、更新约1.5秒；相机当前逐个CPU位姿查询。只验证/优化读取后端，保留语义，不减少任务规模。训练已停23轮，最近保存model_0.pt保留；验证通过后从该正式checkpoint恢复，验证模型不进入正式训练。

性能优化、等价验证及正式恢复完成；训练未结束，未宣称收敛。
