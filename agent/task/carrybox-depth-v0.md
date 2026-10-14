---
task_id: "carrybox-depth-v0"
language: "zh-CN"
axes: ["E", "P", "L", "D"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["SIMULATOR_EXTENSION", "ML_TRAINING", "STATE_MACHINE"]
original_request: "/home/cao/PhysHSI/legged_gym/resources/dataset/dataset_carrybox 参考这个项目的实现 移植到本项目目录下 我想设计一个carrybox任务 只包含用深度图找箱子 然后搬起来的流程 去掉特权信息 观测用深度信息来处理 然后加上一个监督回归的辅助头 用来回归箱子的位姿信息"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/assets/motions/carrybox", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/smoke_carrybox.py", "scripts/rsl_rl/smoke_carrybox.sh", "tests/test_carrybox.py", "docs/carrybox", "README.md", "agent"]
forbidden_scope: ["修改既有踢球任务行为", "长时间训练", "真实硬件", "无关重构"]
steps: ["审查源任务与本地接口", "实现深度拾箱环境与判定", "实现无特权actor/critic与监督位姿头", "接通注册、训练、播放与参考资源", "执行CPU与小规模仿真验证并记录交接"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox.py -v"}, {"command": "bash scripts/rsl_rl/smoke_carrybox.sh"}]
stop_conditions: ["超出允许范围", "真实设备操作", "冻结测试修复两次后仍失败"]
safeguards: ["same-frame depth/labels; reset histories; contact and hold success; finite checks"]
expert_required: true
expert_brief: {"affected_call_path": ["Gym -> CarryBoxEnv -> TiledCamera/proprio/aux labels -> CarryBoxRunner -> PPO"], "critical_interfaces": ["IsaacLab manager obs histories and RSL-RL TensorDict rollout"], "invariants": ["camera ROS frame; meters; wxyz quaternions; no target in actor/critic"], "smallest_change_locus": ["independent carrybox configuration, mdp, learning module"], "mandatory_safeguards": ["same-frame depth/labels; reset histories; contact and hold success; finite checks"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox.py -v", "bash scripts/rsl_rl/smoke_carrybox.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

只新增 carrybox 任务及必要入口；源运动片段作为本地参考归档，不引入原多技能AMP、搬运或放下。actor和critic均读取本体与深度；真值仅供奖励、终止、监督。采用固定场景尺寸与小规模仿真，长训练效果另行验证。
