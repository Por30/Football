---
task_id: "ENG-AGILE-PLAY-COURSE-20260921"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
development_modes: ["BUG_FIX"]
original_request: "你看一下训练指标 对球速的估计误差多少 是否准确 同时新的训练结果 机器人只学到原地站着不懂"
allowed_paths: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/audit_agilekickball.py", "tests/test_agile_play_course.py", "docs/agilekickball/training_audit_20260921", "agent"]
forbidden_scope: ["修改训练奖励/网络/课程定义", "梯度更新或修改旧checkpoint", "真实硬件"]
steps: ["独立于优化器恢复课程状态", "播放load之后reset使第一球采用恢复范围", "CPU验证不加载优化器也恢复进度及真实加载首球", "记录与默认旧播放的对照和剩余感知问题"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agile_play_course.py"}, {"command": "bash scripts/rsl_rl/audit_agilekickball.sh"}]
stop_conditions: ["局部测试两次失败需重新诊断", "超过16环境/3000控制步推理预算"]
safeguards: ["不加载或更新优化器，保留actor权重", "课程加载不瞬移飞行中球；只在play明确reset后发首球", "不将成功代理宣称真实主动接触成功率"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

独立于只读审计的局部修复合同。默认旧播放与训练课程差异已经复现，此处修复与用户站立现象直接相关的接口错误。
