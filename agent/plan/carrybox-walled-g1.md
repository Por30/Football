---
task_id: "carrybox-walled-g1"
language: "zh-CN"
axes: ["E", "P", "L", "D"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/carrybox_walled.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/smoke_carrybox_walled.py", "scripts/rsl_rl/smoke_carrybox_walled.sh", "tests/test_carrybox_walled.py", "docs/carrybox", "projects", "README.md", "agent"]
---

按用户规格新增 G1 walled3 和继承它的 walled4。保留基线与足球接口。X2 完整源码未提供，父奖励沿用本地已验证 G1 基线；未指定的传感器扰动幅度显式记录为本地参数。只运行有限短测。
