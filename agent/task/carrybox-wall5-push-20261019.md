---
task_id: "carrybox-wall5-push-20261019"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "核验用户所述rev13推扰/摩擦差异与完整训练曲线；rev13最新checkpoint三组回放（直接设速度/增量/无推扰），将wall5推扰改为增量并保留课程，地面和sim默认材质设1.0/multiply；非对称critic已完成。"
development_modes: ["SYSTEM_TUNING", "SIMULATOR_EXTENSION"]
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "tests/test_carrybox_push.py", "docs/carrybox/wall5_push_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-push-20261019.md", "agent/task/carrybox-wall5-push-20261019.md", "agent/report/carrybox-wall5-push-20261019.md", "agent/handoff/carrybox-wall5-push-20261019.md"]
forbidden_scope: ["停止/重启/热改正在运行的revision14正式训练", "改动AMP/PPO/RSI/actor/critic/奖励门控/深度噪声/PD/碰撞体", "修改wall3/wall4/football生产行为", "覆盖旧证据、模型、日志或数据"]
steps: ["审计rev13/rev14完整日志及材质/推扰代码", "冻结同checkpoint/seed/步数/动作模式三组回放；实测当前USD绑定和PhysX摩擦", "仅wall5增量推扰和显式摩擦配置，分别验证数学与物理实现并升级契约", "CPU回归与小规模真实仿真/更新/恢复验证；保持正式训练", "汇总分技能回合及删失/推扰时机/材质证据，写回项目和工程记录"]
tests: [{"command": "bash docs/carrybox/wall5_push_20261019/check.sh"}, {"command": "bash docs/carrybox/wall5_push_20261019/replay.sh"}, {"command": "bash docs/carrybox/wall5_push_20261019/smoke.sh"}]
stop_conditions: ["每个失败检查最多范围内修复两次", "GPU显存不足4GiB不启动诊断仿真", "发现checkpoint身份或回放会修改生产训练则停止该验证", "checkpoint身份或严格加载失败、资源不足、需要改动生产训练时停止相关验证；随机流不匹配时不得宣称成对因果"]
safeguards: ["仅wall5后续构造配置改变；当前PID4038923保持，旧运行参数不称新改动已生效", "对照固定同rev13 model10600、16env、1200step、采样动作、seed42、有效迭代10600，其余参数一致", "完成回合与窗口末存活年龄分开；按loco/hold报告，保留每次push前后速度与是否首次推扰前结束；不把历史相关当作因果证据", "rev13回放显式使用原对称网络与完整相同权重；环境物理/传感/RSI与旧契约匹配，新critic不参与回放", "实测USD材质绑定和PhysX接触系数；仅配置推断不能当实际摩擦", "保持1000轮warmup/4000轮ramp，速度增量用world6D/root COM语义与原接口一致", "按新物理契约严格拒绝旧完整resume，旧模型保持；无正式成功率或长期收敛结论", "独立预生成动作/推扰随机流；无推扰保留事件机会；断言初始物理状态一致，之后reset分叉不称严格成对轨迹", "记录回放每次事件的env/skill/age/COM世界速度前值/增量/缓存后值；独立smoke用PhysX get_root_velocities核验set/increment/none与零半满课程、partial IDs和缓存一致，不称回放逐次实测读回", "完成回合与删失年龄按技能分开，总步数每组19200；记录首次push前结束和事件在reset之后的时序", "严格使用原rev13对称网络及完整模型权重和旧环境契约，诊断不运行optimizer或AMP判别器更新", "三组保持旧摩擦，新材质单独smoke；USD地面/default/手脚绑定与PhysX机器人/箱子系数联合核对，默认材质只作用于未绑定形状，不称所有接触系数都为1", "资源检查至少4GiB空闲；只管理诊断子进程；正式PID4038923不停止/重启；保留失败证据"]
expert_required: true
expert_brief: {"affected_call_path": ["wall5 cfg→增量push→root COM PhysX setter；环境checkpoint严格契约；GroundPlane独立材质与physicsScene默认材质"], "critical_interfaces": ["root_vel_w/write_root_velocity_to_sim均为COM世界6D；rev13为对称网络，当前108维critic不兼容；EventManager每回合重采样1–3s推扰，终止reset先于interval事件"], "invariants": ["只改变wall5推扰语义和材质，保留随机范围/间隔/1000+4000课程/RSI/学习/部署；同rev13 model10600/16env/1200步/seed42/有效10600/yaw11.2；当前正式rev14保持运行"], "smallest_change_locus": ["仅mdp/carrybox_wall5.py及carrybox_wall5_env_cfg.py生产代码、定向测试和记录；revision15记录物理契约"], "mandatory_safeguards": ["独立预生成动作/推扰随机流；无推扰保留事件机会；断言初始物理状态一致，之后reset分叉不称严格成对轨迹", "记录回放每次事件的env/skill/age/COM世界速度前值/增量/缓存后值；独立smoke用PhysX get_root_velocities核验set/increment/none与零半满课程、partial IDs和缓存一致，不称回放逐次实测读回", "完成回合与删失年龄按技能分开，总步数每组19200；记录首次push前结束和事件在reset之后的时序", "严格使用原rev13对称网络及完整模型权重和旧环境契约，诊断不运行optimizer或AMP判别器更新", "三组保持旧摩擦，新材质单独smoke；USD地面/default/手脚绑定与PhysX机器人/箱子系数联合核对，默认材质只作用于未绑定形状，不称所有接触系数都为1", "资源检查至少4GiB空闲；只管理诊断子进程；正式PID4038923不停止/重启；保留失败证据"], "minimal_tests": ["bash docs/carrybox/wall5_push_20261019/check.sh", "bash docs/carrybox/wall5_push_20261019/replay.sh", "bash docs/carrybox/wall5_push_20261019/smoke.sh"], "blockers": ["checkpoint身份或严格加载失败、资源不足、需要改动生产训练时停止相关验证；随机流不匹配时不得宣称成对因果"]}
device_actions: []
real_device_authorized: false
---

七字段brief来自wall5_push_review只读专家，补充确认允许独立物理边界smoke读回，不重复整段回放。原三条测试命令和实现范围保持冻结。
