---
task_id: "carrybox-wall5-critic123-aux-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "tests/test_carrybox_asymmetric.py", "tests/test_carrybox_depth_metres.py", "AGENTS.md", "tests/test_carrybox_critic123_aux.py", "docs/carrybox/wall5_critic123_aux_20261021", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-critic123-aux-20261021.md", "agent/task/carrybox-wall5-critic123-aux-20261021.md", "agent/report/carrybox-wall5-critic123-aux-20261021.md", "agent/handoff/carrybox-wall5-critic123-aux-20261021.md"]
artifact: "PLAN"
status: "FROZEN"
---

按用户明确要求，wall5 critic新增双掌/双踝/mid360五个连杆原点相对骨盆位置15维，现有108维尾部追加为123维；rot6定义不变。辅助监督系数1.0，所有配对帧参与；可见性仅诊断。保留米制深度、头高修正、actor边界、RSI及AMP数据。CPU和20环境短测通过后，停止身份匹配的当前4096环境训练，从头启动revision22并验证正式持续更新。
