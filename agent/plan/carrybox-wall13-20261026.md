---
task_id: "carrybox-wall13-20261026"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "PLAN"
status: "READY"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall13_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall13.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/play_carrybox_walled.sh", "docs/carrybox/wall13_20261026", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall13-20261026.md", "agent/task/carrybox-wall13-20261026.md", "agent/report/carrybox-wall13-20261026.md", "agent/handoff/carrybox-wall13-20261026.md"]
---

新增独立wall13，显式使用已找到的用户静止持箱数据，继承wall12全部学习/环境行为。现有canonical findbox revision3已包含300帧静止持箱且与wall12正式checkpoint一致；已向用户说明并询问是否存在更新路径，未得到其他路径前按这一匹配版本实现，不伪称数据发生变化。验收实际配置差异、数据哈希与静止尾段、16环境24步更新和严格恢复。
