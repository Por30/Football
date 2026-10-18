---
task_id: "carrybox-wall5-collision-20261017"
language: "zh-CN"
axes: ["E"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "当前v5任务 看一下g1的碰撞体是什么"
development_modes: ["SIMULATOR_EXTENSION"]
allowed_paths: ["docs/carrybox/wall5_collision_20261017", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-collision-20261017.md", "agent/task/carrybox-wall5-collision-20261017.md", "agent/report/carrybox-wall5-collision-20261017.md", "agent/handoff/carrybox-wall5-collision-20261017.md"]
forbidden_scope: ["修改生产代码/资产/训练参数", "启动仿真/训练或停止后台进程", "把离线USD几何当作已读取PhysX cooked形状"]
steps: ["追踪wall5继承与保存配置", "离线解析USD并在内存执行现有肩部替换函数", "记录逐连杆几何与关键尺寸和自碰撞/遮挡区别", "更新项目入口及交接工件"]
tests: [{"command": "bash docs/carrybox/wall5_collision_20261017/inspect.sh"}]
stop_conditions: ["USD依赖无法解析或资产校验失败时停止，不修改源资产"]
safeguards: ["原USD与生产spawn函数hash前后不变", "仅CPU临时stage，不导入仿真App、不进行PhysX step", "生产spawn函数AST保留原函数体；仅替代stage加载接口", "区分源码/保存配置与运行中PhysX实测"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

单轴T1离线资产核对，主Agent直接完成。仅新增审计工具和证据，不改变现有任务。
