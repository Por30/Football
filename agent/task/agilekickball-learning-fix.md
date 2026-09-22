---
task_id: "ENG-AGILE-LEARNING-20260920"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["BUG_FIX", "STATE_MACHINE"]
original_request: "修复误差记录和恢复发球流程，再评估监督效果 确保策略持续在学习来球踢球的情况"
allowed_paths: ["source/perceptual_ball/perceptual_ball", "scripts/rsl_rl", "tests", "docs/agilekickball", "agent"]
forbidden_scope: ["更改旧checkpoint/参考动作", "真实硬件", "长期训练", "改变actor/critic维度和v0奖励"]
steps: ["实现真实分层误差及有界辅助回溯", "修复首球及保留局内恢复，曝光课程和checkpoint", "CPU验证及仿真短训练和独立评估", "记录结果、限制和训练命令并校验工件"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_learning.py"}, {"command": "bash scripts/rsl_rl/validate_agilekickball_learning.sh"}]
stop_conditions: ["两次失败后停止盲目重试并诊断", "超出128环境/100轮或15分钟训练预算", "真实设备或范围外修改"]
safeguards: ["首球在episode reset初始化；局内重发连续稳定0.3秒，等待至少0.4秒，5秒超时", "标签对齐动作前观测，向量RMSE位置cm速度m/s，空分层count=0不伪造零误差", "回溯恢复参数和Adam；head-only清encoder.grad；记录累计actor KL", "来球曝光按环境数归一化推进课程，保存进度", "保持v0网络维度和奖励语义；短跑不宣称踢球收敛"]
expert_required: true
expert_brief: {"affected_call_path": ["reset/恢复 -> 来球观测 -> rollout -> 辅助更新/指标 -> held-out评估"], "critical_interfaces": ["reset可能有旧reset_buf；父reset动态调用_serve", "minibatch重复epoch不能冒充全样本统计", "先restore optimizer后设置lr"], "invariants": ["首球在episode reset初始化；局内重发连续稳定0.3秒，等待至少0.4秒，5秒超时", "标签对齐动作前观测，向量RMSE位置cm速度m/s，空分层count=0不伪造零误差", "回溯恢复参数和Adam；head-only清encoder.grad；记录累计actor KL", "来球曝光按环境数归一化推进课程，保存进度", "保持v0网络维度和奖励语义；短跑不宣称踢球收敛"], "smallest_change_locus": ["agilekickball状态和配置、algorithm、runner"], "mandatory_safeguards": ["首球在episode reset初始化；局内重发连续稳定0.3秒，等待至少0.4秒，5秒超时", "标签对齐动作前观测，向量RMSE位置cm速度m/s，空分层count=0不伪造零误差", "回溯恢复参数和Adam；head-only清encoder.grad；记录累计actor KL", "来球曝光按环境数归一化推进课程，保存进度", "保持v0网络维度和奖励语义；短跑不宣称踢球收敛"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_learning.py", "bash scripts/rsl_rl/validate_agilekickball_learning.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

单个只读L+D专家审查通过，无blocker。旧训练进程不自动停止。首球区别于局内恢复，从0.5–0.7m起物理滚动，保留原终止与奖励。覆盖计数与成功代理分开记录。
