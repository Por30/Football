---
task_id: "carrybox-wall5-rsi-pickup5-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "docs/carrybox/wall5_rsi_pickup5_20261021", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-rsi-pickup5-20261021.md", "agent/task/carrybox-wall5-rsi-pickup5-20261021.md", "agent/report/carrybox-wall5-rsi-pickup5-20261021.md", "agent/handoff/carrybox-wall5-rsi-pickup5-20261021.md"]
artifact: "TASK"
original_request: "rsi reset在从loco部分分出 5%来pick up把"
development_modes: ["SYSTEM_TUNING"]
forbidden_scope: ["不修改AMP数据或专家比例、PPO、观测、奖励、物理", "不启动、停止或重启正式训练", "不修改wall3/wall4/football行为"]
steps: ["保存当前配置与进程身份", "将wall5 RSI默认改为75/5/20并修正配额说明", "运行实际20环境reset与4096配额检查", "记录兼容性和训练生效边界并更新项目入口"]
tests: [{"command": "bash docs/carrybox/wall5_rsi_pickup5_20261021/check.sh"}]
stop_conditions: ["显存不足4096MiB停止短测", "非有限状态或CUDA错误停止", "范围内最多两次失败修复"]
safeguards: ["pickup仅用既有0–31帧，箱底5mm间隙，无平台", "hold20%保留手边参考箱高", "已有契约记录reset_probs和reset_skill_probabilities，不绕过严格恢复检查", "后台PID570043保持运行，源码配置不热更新"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

仅修改wall5 RSI默认分配为75/5/20，复用固定配额与既有贴地pickup采样。AMP、物理、观测、奖励和后台训练保持。验收实际配置/4096配额、20环境全部/部分/自动reset、旧新契约差异。
