---
task_id: "carrybox-wall5-hold-rsi-20261017"
language: "zh-CN"
axes: ["E"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "改成0.2是hold"
development_modes: ["SYSTEM_TUNING", "SIMULATOR_EXTENSION"]
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "tests/test_carrybox_ground.py", "projects/README.md", "projects/findbox/README.md", "docs/carrybox/wall5_hold_rsi_20261017", "agent/plan/carrybox-wall5-hold-rsi-20261017.md", "agent/task/carrybox-wall5-hold-rsi-20261017.md", "agent/report/carrybox-wall5-hold-rsi-20261017.md", "agent/handoff/carrybox-wall5-hold-rsi-20261017.md"]
forbidden_scope: ["修改AMP数据、PPO、深度、碰撞体或wall3/4行为", "启动/停止正式训练或实机动作"]
steps: ["更改wall5 RSI为80/0/20并恢复hold参考箱高", "更新reset契约与针对性检查", "小环境验证并记录项目状态"]
tests: [{"command": "bash docs/carrybox/wall5_hold_rsi_20261017/check.sh"}, {"command": "bash docs/carrybox/wall5_hold_rsi_20261017/smoke.sh"}]
stop_conditions: ["显存不足4096MiB不启动GPU短测", "仿真非有限或CUDA错误", "同一检查修复两次仍失败"]
safeguards: ["仅wall5显式允许hold保留参考箱位置；默认ground任务继续拒绝hold", "不修改原数据/AMP比例；loco仍贴地，pickup概率0", "部分reset不改变存活环境；旧checkpoint契约拒绝；不操作后台训练"]
expert_required: false
device_actions: []
real_device_authorized: false
---

仅E轴reset分布局部修改。用户最新指令覆盖之前hold为0的设置；hold不能仍将箱子强制落地。
