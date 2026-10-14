---
task_id: "AGILE-V3-AIM035-20260928"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "tests/test_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "docs/agilekickball_v3/README.md", "docs/agilekickball_v3/aim035_20260928", "README.md", "agent/plan/agilekickball-v3-aim035.md", "agent/task/agilekickball-v3-aim035.md", "agent/report/agilekickball-v3-aim035.md", "agent/handoff/agilekickball-v3-aim035.md"]
development_modes: ["SYSTEM_TUNING"]
original_request: "来球横向目标成成 +\\_ 0.35m"
forbidden_scope: ["改变距离、移动边界、球速、奖励或网络", "停止或重启训练", "修改历史checkpoint及验证结果"]
steps: ["确认v3横向课程及版本", "将最终横向目标范围收窄到±0.35m并同步既有测试和说明", "执行既有回归并保存报告交接"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py"}]
stop_conditions: ["两次范围内修复后冻结测试仍失败", "需要扩大范围"]
safeguards: ["保留初始±0.25m与60000步曝光课程", "保持空间单位和坐标系", "更新revision和存档配置以拒绝旧分布checkpoint", "不操作已有训练进程"]
expert_required: false
device_actions: []
real_device_authorized: false
---

仅调整横向目标空间参数组：最终半宽0.75→0.35m，中点0.50→0.30m，起点0.25m不变。更新v3 revision、现有测试期望与当前说明；历史验证保留。T1由当前Agent直接执行既有回归。
