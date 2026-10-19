---
task_id: "carrybox-wall5-roll05-20261019"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "roll终止改成0.5把 并说明0.8和0.5的区别"
development_modes: ["SYSTEM_TUNING"]
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "tests/test_carrybox_training_v12.py", "docs/carrybox/wall5_roll05_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-roll05-20261019.md", "agent/task/carrybox-wall5-roll05-20261019.md", "agent/report/carrybox-wall5-roll05-20261019.md", "agent/handoff/carrybox-wall5-roll05-20261019.md"]
forbidden_scope: ["不恢复上次未通过的PD/腿姿/课程修复候选", "不改pitch阈值、其他任务、数据、奖励权重、观察或网络", "不启动、停止或恢复训练，不宣称修复行走或收敛"]
steps: ["核对wall5终止调用及checkpoint契约", "仅roll阈值及契约改为0.5并同步既有边界检查", "运行针对性CPU检查并记录新旧阈值含义", "更新项目入口及工程工件"]
tests: [{"command": "bash docs/carrybox/wall5_roll05_20261019/check.sh"}]
stop_conditions: ["针对性检查失败最多两次范围内修复", "出现范围外差异则保留现场停止，不启动GPU训练"]
safeguards: ["保留双向abs及严格大于语义，pitch仍1.1rad", "保留此前未提交改动和旧模型数据", "同步roll_termination与roll_limit，旧模型不伪装相同环境契约"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

独立执行用户新指定的单参数变更；不重开此前耗尽修正次数的loco控制修复。采用已有边界测试，不新增仿真或长训。
