---
task_id: "carrybox-wall4-warp"
language: "zh-CN"
axes: ["P", "A"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_raycast.py", "source/perceptual_ball/perceptual_ball/carrybox_warp_camera.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/benchmark_carrybox_warp.py", "scripts/rsl_rl/benchmark_carrybox_warp.sh", "tests/test_carrybox_raycast.py", "docs/carrybox/warp_20261014", "docs/carrybox/render6s_20261014/launch.json", "README.md", "projects/README.md", "projects/findbox/README.md", "agent", "logs/rsl_rl/g1_carrybox_depth/walled4", "scripts/rsl_rl/smoke_carrybox_walled.py", "scripts/rsl_rl/train.py"]
artifact: "PLAN"
status: "DONE"
---

用户要求迁移动态Warp深度并先验收速度再开正式训练。使用wall4_perf_review唯一只读专家。足球真实日志约2.47秒但仅球解析深度，不能移植其遮挡简化。当前Wall4已发SIGINT且进程退出，旧正式模型保留。新契约区分RTX与Warp，warm-start不继承旧AMP optimizer。

2026-10-14验收适配增补：旧geometry脚本直接读取RTX私有_view.get_local_poses，Warp没有该RTX对象。仅加入Warp局部mount读取分支，断言、测试命令及停止条件不变；原Task保留docs，属harness接口适配，不改变生产场景。
正式warm-start失败后的最小范围补充：train.py仅CarryBox分支在写initialization.json前创建log_dir，沿用相邻football分支相同逻辑，不改共享训练算法。补真实分支CPU回归，测试命令和门槛不变。
