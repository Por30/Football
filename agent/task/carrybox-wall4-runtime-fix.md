---
task_id: "carrybox-wall4-runtime-fix"
language: "zh-CN"
axes: ["E", "L", "A"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "修复环境等等问题 确保wall4正式训练练能够正常起来"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "scripts/rsl_rl/diagnose_carrybox_walled.py", "scripts/rsl_rl/diagnose_carrybox_walled.sh", "scripts/rsl_rl/smoke_carrybox_walled.py", "scripts/rsl_rl/smoke_carrybox_walled.sh", "scripts/rsl_rl/validate_carrybox_runtime.sh", "scripts/rsl_rl/queue_wall4.py", "scripts/rsl_rl/train_carrybox_walled.sh", "tests/test_carrybox_queue.py", "tests/test_carrybox_walled.py", "docs/carrybox/wall4_repair", "docs/carrybox/walled/README.md", "projects", "README.md", "agent", "logs/rsl_rl/g1_carrybox_depth"]
forbidden_scope: ["更改football训练行为", "移动删除原始数据或已有模型", "关闭碰撞/RSI/AMP作为生产绕过", "修改系统IsaacLab或驱动安装", "未授权真实设备"]
development_modes: ["BUG_FIX", "SIMULATOR_EXTENSION", "TOOLING"]
steps: ["隔离PPO、reset、碰撞及测试探针定位故障", "修正证实问题并保持观测及任务合同", "执行CPU合同与真实连续训练验收", "验证128环境正式规模及资源", "更新等待器绑定新回执源码并串行启动wall4", "验证正式启动或保存等待状态并更新项目工件"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}, {"command": "bash scripts/rsl_rl/validate_carrybox_runtime.sh"}, {"command": "/home/cao/ENTER/envs/ball/bin/python scripts/rsl_rl/queue_wall4.py --check-only"}]
stop_conditions: ["两次范围内实现修复后冻结验收仍失败", "需要停止football或操作真实设备", "GPU资源不足时等待，不强制启动", "正式启动身份不明或源码/数据/回执不匹配"]
safeguards: ["不停止或重启football；只管理本轮自己创建的测试/等待器/训练进程", "不删除碰撞或感知/AMP/RSI要求作为正式配置的变通", "4环境诊断先行；128环境必须有内存余量或等待football结束", "真实runner连续更新/保存/恢复/多次reset与传感器几何检查，不能只证明静态render", "只有最终football模型验证和wall4目标规模短测通过才能一次性正式启动；不得伪造旧PASS或自动重试长训"]
expert_required: true
expert_brief: {"affected_call_path": ["walled环境重置、障碍碰撞、PhysX张量API、相机与真实PPO runner；独立队列启动"], "critical_interfaces": ["PhysX frontend保证float32/indices int32连续，不应把非连续切片直接认定根因", "真实runner.learn必须跨更新、保存和reset"], "invariants": ["actor/critic只含本体与深度；真值只作监督/奖励", "保持football接口和已有进程"], "smallest_change_locus": ["定点诊断分离环境、学习、探针；只改确证因果路径", "walled任务及其启动/验证脚本"], "mandatory_safeguards": ["不停止或重启football；只管理本轮自己创建的测试/等待器/训练进程", "不删除碰撞或感知/AMP/RSI要求作为正式配置的变通", "4环境诊断先行；128环境必须有内存余量或等待football结束", "真实runner连续更新/保存/恢复/多次reset与传感器几何检查，不能只证明静态render", "只有最终football模型验证和wall4目标规模短测通过才能一次性正式启动；不得伪造旧PASS或自动重试长训"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "bash scripts/rsl_rl/validate_carrybox_runtime.sh", "/home/cao/ENTER/envs/ball/bin/python scripts/rsl_rl/queue_wall4.py --check-only"], "blockers": ["两次范围内实现修复后冻结验收仍失败", "需要停止football或操作真实设备", "GPU资源不足时等待，不强制启动", "正式启动身份不明或源码/数据/回执不匹配"]}
device_actions: []
real_device_authorized: false
---

新授权继续修复wall4 GPU训练故障。先做可控诊断建立根因证据，再改最小必要路径；验收不限首次迭代，必须持续跨更新/保存/重置，并保留场景遮挡与纯感知策略输入。正式训练沿用用户已授权的football完成后串行安排。唯一只读专家已核对PhysX张量frontend的连续类型转换，未发现重复索引，不据此改系统库。
