---
task_id: "carrybox-wall5-critic123-aux-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "tests/test_carrybox_asymmetric.py", "tests/test_carrybox_depth_metres.py", "AGENTS.md", "tests/test_carrybox_critic123_aux.py", "docs/carrybox/wall5_critic123_aux_20261021", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-critic123-aux-20261021.md", "agent/task/carrybox-wall5-critic123-aux-20261021.md", "agent/report/carrybox-wall5-critic123-aux-20261021.md", "agent/handoff/carrybox-wall5-critic123-aux-20261021.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "critic108多出的15维末端位置，以及辅助监督改为1.0所有帧，这两项也加上，然后重启训练。"
development_modes: ["ML_TRAINING"]
forbidden_scope: ["不改足球、wall3/4、actor输入或导出接口", "不改数据集、RSI75/5/20、物理资产、相机、奖励或控制", "不删除旧日志模型、不恢复旧checkpoint"]
steps: ["冻结输入/损失语义与当前训练身份", "最小改动实现critic123和全帧辅助监督1.0并版本化契约", "CPU验证frame/信息隔离/损失梯度及20环境更新恢复导出", "通过后停止旧PID并正式fresh4096环境", "验证正式迭代有限性/6秒性能、写回工程记录"]
tests: [{"command": "bash docs/carrybox/wall5_critic123_aux_20261021/validate_and_restart.sh"}]
stop_conditions: ["CPU或仿真失败不停止旧训练；范围内最多修复两次", "旧进程身份不符、源码或数据变动不启动", "新训练非有限、契约不符停止验收且不重复启动"]
safeguards: ["五个G1连杆原点，位置单位米，pelvis link坐标系，有序映射", "123维仅进入独立critic MLP及终止前bootstrap，actor和部署仍仅深度与本体", "可见/不可见/超量程都监督；标签仍与深度捕获延迟冻结严格配对，不截断目标", "checkpoint revision22拒绝旧108维/掩码损失模型；从头训练", "先离线及20env短测，再身份检查停止旧进程；保留历史并检查新run4096更新/性能"]
expert_required: false
device_actions: []
real_device_authorized: false
---

按用户明确要求，wall5 critic新增双掌/双踝/mid360五个连杆原点相对骨盆位置15维，现有108维尾部追加为123维；rot6定义不变。辅助监督系数1.0，所有配对帧参与；可见性仅诊断。保留米制深度、头高修正、actor边界、RSI及AMP数据。CPU和20环境短测通过后，停止身份匹配的当前4096环境训练，从头启动revision22并验证正式持续更新。
