---
task_id: "AGILE-V3-20260927"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_state.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "tests/test_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "docs/agilekickball_v3", "README.md", "agent/plan/agilekickball-v3.md", "agent/task/agilekickball-v3.md", "agent/report/agilekickball-v3.md", "agent/handoff/agilekickball-v3.md"]
development_modes: ["SYSTEM_TUNING"]
original_request: "在v2 基础上新建v3 发球距离最远到3m 来球到机器人身边的位置再大一些 离开远一些也可以"
forbidden_scope: ["修改v0/v1/v2行为或奖励/PPO/网络", "启动长期训练、修改已有checkpoint", "实机操作"]
steps: ["核对v2课程与发球几何及离锚点限制", "新增v3任务及渐进3m距离、横向目标偏移和移动边界", "保存独立课程版本并复用v2速度/恢复流程", "运行发球几何、课程存取、旧版本回归及真实CPU仿真/PPO短测", "补充设计与训练命令、报告和交接"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v3.sh"}]
stop_conditions: ["冻结测试两次范围内修复后仍失败", "需要实机或长期训练", "需要扩大改动范围"]
safeguards: ["保持球速单位m/s、空间单位m、原发球平面坐标系", "共享发球采样默认值及随机数调用顺序不变", "保持5秒恢复超时、非有限值检查、终止优先和play冻结", "v3独立checkpoint key/config，旧课程在权重加载前拒绝", "最远3m来球不可立即被球结束边界截断；部分reset不改变其他环境", "短测不代表宽范围高速策略已经学成"]
expert_required: false
device_actions: []
real_device_authorized: false
---

横向偏移相对初始站位、沿发球径向的垂直方向采样；不是球在世界坐标系的固定Y位置。保持episode anchor固定，不改成跟随机器人。共享serve与球结束判断读取实例级偏移范围及球最大半径，默认保持原值。v3球结束半径3→4m，为3m发球和向外回球留余量。独立v3课程键与revision防止旧checkpoint静默套用新分布；默认从零训练。
