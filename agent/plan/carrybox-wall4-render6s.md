---
task_id: "carrybox-wall4-render6s"
language: "zh-CN"
axes: ["P", "A"]
risk_tier: "T2"
artifact: "PLAN"
status: "ACTIVE"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/carrybox_camera.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/benchmark_carrybox_render.py", "scripts/rsl_rl/benchmark_carrybox_render.sh", "tests/test_carrybox_camera.py", "docs/carrybox/render6s_20261014", "docs/carrybox/performance_20261014", "projects/README.md", "projects/findbox/README.md", "README.md", "agent", "logs/rsl_rl/g1_carrybox_depth/walled4"]
---

目标为4096环境×24控制步的完整训练迭代<=6秒。前版约21秒，继续按真实profile优化渲染/场景更新；不承诺未验证倍率。用户被可选询问6秒参考配置，工作不依赖答复。复用wall4_perf_review单个只读专家，4.5 FSD支持已核对本机头文件/官方测试。

运行证据修正：4.5有FSD插件但物理仿真不支持。加载delegate后omni.physxstageupdate明确禁用physics，已撤回FSD；后续候选保持传统delegate，只缓存静态mount并使用depth-only渲染配方。
