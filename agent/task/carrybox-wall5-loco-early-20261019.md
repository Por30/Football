---
task_id: "carrybox-wall5-loco-early-20261019"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "用户反馈没抱箱时一开始就reset、尚未学会移动；排查行走起点前20步失败原因"
development_modes: ["SYSTEM_TUNING", "MODEL_DEPLOYMENT"]
allowed_paths: ["docs/carrybox/wall5_loco_early_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-loco-early-20261019.md", "agent/task/carrybox-wall5-loco-early-20261019.md", "agent/report/carrybox-wall5-loco-early-20261019.md", "agent/handoff/carrybox-wall5-loco-early-20261019.md"]
forbidden_scope: ["修改生产环境/奖励/RSI/AMP/网络/数据", "停止重启或启动正式训练", "把参考轨迹或持箱RSI存活称作已学会地面拾箱"]
steps: ["核对当前运行状态、model11200和参考初始化/动作/奖励路径", "同种子同初态16环境100步对照策略均值/保持参考q/默认q/参考轨迹/保持参考q清初速，记录首终止及前20步", "核对完整训练日志分技能采样占比/奖励尺度与动作夹限", "按证据归因并记录已知局限及后续最小修复方向"]
tests: [{"command": "bash docs/carrybox/wall5_loco_early_20261019/check.sh"}, {"command": "bash docs/carrybox/wall5_loco_early_20261019/replay.sh"}]
stop_conditions: ["每个失败检查最多两次范围内修复", "少于4GiB可用显存不启动诊断", "checkpoint或归档环境契约不匹配则停止", "模型/环境身份、finite、初态或观察严格配对失败时停止依赖它的因果比较，不弱化断言。", "无真实源帧或参考末尾未标记时不能做轨迹控制归因。", "生产代码修改或正式重训超出本次诊断范围。"]
safeguards: ["仅诊断子进程，用真实rev14 model11200严格加载；当前正式训练进程已不存在，不推断退出原因", "保持物理/噪声/原推扰与终止；仅诊断集中loco初始化，reset概率生产80/0/20不改", "以每个环境首次失败为统计单位，完成/100步存活分开；记录实际push时机，首20步不归因于尚未施加的push", "控制组通过同一动作处理链映射目标，保留真实clip与物理限位并记录；初速清零为显式独立条件", "核对真实clip/frame及q/qdot映射和PhysX回读；root link/COM速度、箱/障碍/相机/offset及actor初始观察同条件配对，清初速仅单独显式条件。", "记录前20步原策略/输入/动作裁剪/限位前后目标、q/qdot/限位/PD/力矩与足端接触，按腿/腰分解。", "终止/奖励必须在reset前捕获；只比较每环境首次终止，100步存活为截尾，不混入reset后轨迹。", "保留实际push并记录时机，首20步与更长含push样本分开；参考轨迹到末尾保持必须标记并分开解释。", "原始task、dt和混合系数区分；未加载D时不声称总混合回报；初始带速度冻结参考失败不证明初始化必错。", "资源下限4GiB与固定超时，诊断结束释放，权重逐项确认不变，不停止其他进程。"]
expert_required: true
expert_brief: {"affected_call_path": ["归档rev14 config/env → shared WalledCarryBoxEnv → WalledJointPositionAction → PD/PhysX；所有对照走同一动作处理链。", "reset_scene → initialize_reference → FindBoxMotionLibrary → root/joint写入 → sim.forward → 足底几何校正 → 箱子/障碍/相机；每policy步物理、termination、reward、reset、interval push、obs。", "奖励项乘0.02s后进入task，训练混合0.75 task + 0.125 style。"], "critical_interfaces": ["源29关节依SOURCE_JOINT_NAMES按名称映射；qdot与root速度来自60Hz差分，区分root link与COM速度。", "动作offset是经±0.01随机化的默认角，zero action不是RSI角；wrapper ±9，scale0.25，之后物理限位。", "参考角跟踪用下一policy时刻60→50Hz插值；片段末尾明确标记；带步态初速冻结q不是静态站立对照。", "源base_height与base_position.z可能不一致；PD速度目标为0而初始化qdot非零，保留记录，不自动改生产实现。", "足底初始接触力0可能来自5mm间隙/缓存，并不能证明无碰撞；roll0.8/pitch1.1、root0.2/headCOM0.4终止。"], "invariants": ["只读strict model11200/rev14，不混入当前rev15推扰摩擦；生产RSI80/0/20保持。", "actor深度/本体，critic独立108维；不写共享代码、数据、权重或改变训练进程。", "比较真正首回合终止前状态，后续autoreset回合不冒充独立同初态样本。"], "smallest_change_locus": ["docs/carrybox/wall5_loco_early_20261019内临时CPU审计与短仿真记录器；允许的项目入口与四工件。", "同进程重复reset深度不一致时，使用独立进程消除跨条件缓存，不覆盖观测、不放宽断言。"], "mandatory_safeguards": ["核对真实clip/frame及q/qdot映射和PhysX回读；root link/COM速度、箱/障碍/相机/offset及actor初始观察同条件配对，清初速仅单独显式条件。", "记录前20步原策略/输入/动作裁剪/限位前后目标、q/qdot/限位/PD/力矩与足端接触，按腿/腰分解。", "终止/奖励必须在reset前捕获；只比较每环境首次终止，100步存活为截尾，不混入reset后轨迹。", "保留实际push并记录时机，首20步与更长含push样本分开；参考轨迹到末尾保持必须标记并分开解释。", "原始task、dt和混合系数区分；未加载D时不声称总混合回报；初始带速度冻结参考失败不证明初始化必错。", "资源下限4GiB与固定超时，诊断结束释放，权重逐项确认不变，不停止其他进程。"], "minimal_tests": ["bash docs/carrybox/wall5_loco_early_20261019/check.sh", "bash docs/carrybox/wall5_loco_early_20261019/replay.sh"], "blockers": ["模型/环境身份、finite、初态或观察严格配对失败时停止依赖它的因果比较，不弱化断言。", "无真实源帧或参考末尾未标记时不能做轨迹控制归因。", "生产代码修改或正式重训超出本次诊断范围。"]}
device_actions: []
real_device_authorized: false
---

只读诊断完成。七字段brief与跟进意见已归档继承，原始范围、步骤和两条测试命令保持；补嵌入前Task保留在docs。五条件使用独立进程，不放宽初态或观察断言。
