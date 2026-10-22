---
task_id: "carrybox-wall5-walk-diagnosis-20261022"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
status: "FROZEN"
allowed_paths: ["docs/carrybox/wall5_walk_diagnosis_20261022", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-walk-diagnosis-20261022.md", "agent/task/carrybox-wall5-walk-diagnosis-20261022.md", "agent/report/carrybox-wall5-walk-diagnosis-20261022.md", "agent/handoff/carrybox-wall5-walk-diagnosis-20261022.md"]
artifact: "TASK"
original_request: "为什么训了那么久 感觉走路不不会呢"
development_modes: ["MODEL_DEPLOYMENT"]
forbidden_scope: ["不改生产源码、数据、checkpoint或正式训练进程", "不把只读回放对照当作重新训练的因果证明"]
steps: ["锁定进程和模型源码身份，提取两轮同阶段训练曲线", "复用严格网络加载，隔离场景比较开关自碰撞及推扰并加入旧模型与保持reset角基线", "检查first-episode终止、接触及动作证据，区分事实和待证原因", "写入诊断和项目入口，复核正式进程和文件未变"]
tests: [{"command": "bash docs/carrybox/wall5_walk_diagnosis_20261022/check.sh"}]
stop_conditions: ["可用显存低于6GiB不启动仿真", "身份不符、NaN或PhysX错误停止，范围内最多修复两次并保留失败记录"]
safeguards: ["仅独立仿真实例覆写自碰撞/推扰；记录所有契约差异", "基线rev23严格契约，旧模型仅用于明确标注的同网络权重对照", "固定seed42，记录首回合含右删失，不能把短回合偏差写成长期成功率", "后台训练保持；记录源码和模型hash及PID身份"]
expert_required: false
device_actions: []
real_device_authorized: false
---

核对revision23行走失稳，比较训练曲线及固定checkpoint在隔离仿真中的自碰撞/推扰对照，读取动作、接触与终止证据。生产源码、正式训练与历史数据不变；这是工程诊断，不是训练收敛或总体成功率评估。
