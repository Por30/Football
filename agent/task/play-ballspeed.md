---
task_id: "ENG-PLAY-BALLSPEED-20260921"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
development_modes: ["CLI_INTERFACE"]
original_request: "修改play 增加一个可选的来球速度参数 --ballspeed min max"
allowed_paths: ["scripts/rsl_rl/play.py", "scripts/rsl_rl/cli_args.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_state.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v1.py", "tests/test_play_ballspeed.py", "docs/agilekickball_v1", "agent"]
forbidden_scope: ["修改训练默认速度或奖励/网络", "长训练或真实硬件"]
steps: ["添加双浮点参数及有限正数/顺序校验", "模型加载后覆盖，首球reset及v1统一范围采样", "验证无参数默认、固定速度、范围覆盖与多次reset", "文档和工件校验"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_play_ballspeed.py"}]
stop_conditions: ["范围外修改", "两次失败后诊断"]
safeguards: ["0<min<=max且有限，允许min=max固定速度", "仅play设置运行时override，checkpoint课程不被改写", "v1覆盖时冻结课程更新且绕过挑战区间混合，后续reset仍使用覆盖范围"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

T1局部参数和采样接口修改，使用现有真实状态类的边界测试；不需要专家或长仿真训练。
