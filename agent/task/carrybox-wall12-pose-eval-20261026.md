---
task_id: "carrybox-wall12-pose-eval-20261026"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "停掉后台练练，给wall12指定model_19999.pt的play命令，同时看回归箱子信息的误差"
allowed_paths: ["docs/carrybox/wall12_pose_eval_20261026", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall12-pose-eval-20261026.md", "agent/task/carrybox-wall12-pose-eval-20261026.md", "agent/report/carrybox-wall12-pose-eval-20261026.md", "agent/handoff/carrybox-wall12-pose-eval-20261026.md"]
forbidden_scope: ["修改生产代码、checkpoint、训练日志或参数", "重启正式训练或无关任务", "把训练MSE直接解释为角度", "把单seed逐帧诊断称为总体成功率或实机精度"]
development_modes: ["MODEL_DEPLOYMENT"]
steps: ["核对进程、最终checkpoint及完整训练日志，必要时停止已识别训练", "读取损失趋势、验证误差换算和对称角度计算", "固定64环境1000步seed12345均值动作回放，逐帧保存预测真值并按可见性和持箱分层", "交付play命令和有单位的误差统计，更新正式训练完成状态"]
tests: [{"command": "bash docs/carrybox/wall12_pose_eval_20261026/check_cpu.sh"}, {"command": "bash docs/carrybox/wall12_pose_eval_20261026/evaluate.sh"}]
stop_conditions: ["checkpoint契约或身份不匹配", "出现非有限预测/标签或采样配对错误", "GPU资源不足", "两次局部脚本修复后验收仍失败"]
safeguards: ["64×1000样本按帧统计，明确回放分布和训练采样不同", "预测9维位姿，尺寸仅决定对称集合，不能声称预测了尺寸", "旋转6D先正交化，再按实际尺寸允许的旋转对称求最小角度，退化输出单独计数", "几何可见性用箱体射线深度与真实干净场景深度比较，不把任意近深度当箱子", "保留噪声/墙柱/随机reset和物理扰动，使用同一时刻预测标签", "不改写任何已有模型日志；当前无后台训练则记录无需停止"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

单学习轴只读诊断与有限回放，主Agent直接执行。最终checkpoint路径固定为用户指定2026-10-25_12-32-53_wall12_24step_pose_aux_fresh_20261025_123249/model_19999.pt。
