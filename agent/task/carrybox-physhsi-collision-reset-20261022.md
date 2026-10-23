---
task_id: "carrybox-physhsi-collision-reset-20261022"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T1"
status: "FROZEN"
allowed_paths: ["docs/carrybox/physhsi_collision_reset_20261022", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-physhsi-collision-reset-20261022.md", "agent/task/carrybox-physhsi-collision-reset-20261022.md", "agent/report/carrybox-physhsi-collision-reset-20261022.md", "agent/handoff/carrybox-physhsi-collision-reset-20261022.md"]
artifact: "TASK"
original_request: "你看下 ~/physHSI 里面关于碰撞和reset是什么逻辑 和这里有什么区别"
development_modes: ["SIMULATOR_EXTENSION", "ML_DATA_PIPELINE"]
forbidden_scope: ["不改任一仓库生产源码、资产、数据或模型", "不启动GPU仿真或停止/重启正式训练"]
steps: ["沿实际任务注册读取两套生效配置和调用路径", "CPU解析URDF碰撞体、执行纯配置继承并核对RSI概率及源速度", "区分已注册奖励/终止与未启用函数，记录差异和影响边界", "保存证据及四工件，更新项目入口"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/physhsi_collision_reset_20261022/audit.py"}]
stop_conditions: ["相关源码身份变化或解析不符停止并报告", "最多两次原范围修复，保留失败回执"]
safeguards: ["PhysHSI只读，按carrybox而非其他任务默认值解释", "不把权重数组当作归一化概率，不把定义但未注册的函数当作生效项", "不把Isaac Gym与Isaac Lab碰撞导入结果直接认作完全相同", "文件hash和引用行号可复查，记录只读范围"]
expert_required: false
device_actions: []
real_device_authorized: false
---

只读核对本地PhysHSI的G1 carrybox/carrybox_resume与当前wall5 revision23的碰撞几何、自碰撞、接触惩罚、RSI状态/速度/延迟缓存、终止与箱子reset。解析真实配置与URDF，保存代码位置和CPU证据；不修改生产代码、数据或训练进程，不以源码核对冒充PhysHSI动态验证。
