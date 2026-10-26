---
task_id: "carrybox-wall12-tf32-20261025"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "停止足球 启动wall12；修复启动时发现的wall12回归块TF32非有限损失以完成正式启动"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall12.py", "tests/test_carrybox_wall12_tf32.py", "docs/carrybox/wall12_start24_20261025/tf32_fix", "agent/plan/carrybox-wall12-tf32-20261025.md", "agent/task/carrybox-wall12-tf32-20261025.md", "agent/report/carrybox-wall12-tf32-20261025.md", "agent/handoff/carrybox-wall12-tf32-20261025.md"]
forbidden_scope: ["修改共享PPO、相机、actor/critic、奖励或采样配方", "关闭全局TF32、放宽尺寸容差、过滤坏样本或屏蔽非有限检查", "改变回归坐标系、维度或损失定义", "覆盖首个失败run和历史证据"]
development_modes: ["ML_TRAINING"]
steps: ["保存首个失败run并复现大批量TF32对尺寸轴置换的影响", "用精确轴索引替代尺寸矩阵乘法，保留物理对称判定", "运行CPU回归和CUDA TF32大批前后向测试", "记录修复身份与限制，交回原正式启动任务"]
tests: [{"command": "bash docs/carrybox/wall12_start24_20261025/tf32_fix/check_cpu.sh"}, {"command": "bash docs/carrybox/wall12_start24_20261025/tf32_fix/check_cuda.sh"}]
stop_conditions: ["修复需要改变损失定义或其他任务", "两次局部修复后检查仍失败", "出现未解释非有限值"]
safeguards: ["TF32训练开关保持原样，仅移除精确分类中的浮点矩阵乘法", "非方箱90度不能误作对称，尺寸容差不变", "验证4/8/24候选数、TF32开关不影响mask、8192样本损失与梯度有限", "保留首轮失败log与原源码身份，不用docs模型启动正式训练"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

单文件局部修复，T1学习轴，主Agent直接完成。该修复是用户授权启动任务的必要故障修复；不会借机改变此前讨论的回归目标或其他训练参数。
