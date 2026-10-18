---
task_id: "agilekickball-v5-no-randomization-20261017"
language: "zh-CN"
axes: ["C", "P"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "去掉v5 kpkd随机化 和深度噪声"
development_modes: ["SYSTEM_TUNING"]
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v5_env_cfg.py", "scripts/rsl_rl/smoke_agilekickball_v5.py", "README.md", "projects/README.md", "projects/football/README.md", "docs/agilekickball_v5/README.md", "docs/agilekickball_v5/randomization/README.md", "docs/agilekickball_v5/no_randomization_20261017", "agent/plan/agilekickball-v5-no-randomization-20261017.md", "agent/task/agilekickball-v5-no-randomization-20261017.md", "agent/report/agilekickball-v5-no-randomization-20261017.md", "agent/handoff/agilekickball-v5-no-randomization-20261017.md"]
forbidden_scope: ["修改v4/CarryBox/共享资产、奖励或网络", "停止、启动或恢复正式训练", "删除旧模型或绕过checkpoint合同"]
steps: ["核对现有关闭路径与旧checkpoint合同", "关闭v5两个默认开关，历史随机化短测显式启用原场景", "执行已有CPU检查并核对改动", "同步项目入口、看板与工程记录"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p 'test_agilekickball_v5*.py' -v"}]
stop_conditions: ["需要修改共享实现或checkpoint恢复语义", "测试失败两次范围内修复后仍未通过"]
safeguards: ["保留场景光轴深度、自遮挡和现有物理/学习参数", "关闭增益时使用现有倍率1路径，关闭噪声时直接返回clean深度", "保留显式开关和范围以支持旧带扰动模型精确恢复", "不操作训练进程，不启动GPU仿真"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

用户要求去掉v5的Kp/Kd随机化与深度噪声。保留实现以便显式恢复历史实验，默认新建训练/播放采用固定名义增益及无噪声场景深度。旧模型合同不同会被严格拒绝，不自动迁移或重训。
