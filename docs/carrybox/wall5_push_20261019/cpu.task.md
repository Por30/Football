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
tests: [{"command": "bash docs/carrybox/wall5_push_20261019/check.sh"}]
stop_conditions: ["每个失败检查最多范围内修复两次", "GPU显存不足4GiB不启动诊断仿真", "发现checkpoint身份或回放会修改生产训练则停止该验证"]
safeguards: ["仅wall5后续构造配置改变；当前PID4038923保持，旧运行参数不称新改动已生效", "对照固定同rev13 model10600、16env、1200step、采样动作、seed42、有效迭代10600，其余参数一致", "完成回合与窗口末存活年龄分开；按loco/hold报告，保留每次push前后速度与是否首次推扰前结束；不把历史相关当作因果证据", "rev13回放显式使用原对称网络与完整相同权重；环境物理/传感/RSI与旧契约匹配，新critic不参与回放", "实测USD材质绑定和PhysX接触系数；仅配置推断不能当实际摩擦", "保持1000轮warmup/4000轮ramp，速度增量用world6D/root COM语义与原接口一致", "按新物理契约严格拒绝旧完整resume，旧模型保持；无正式成功率或长期收敛结论"]
expert_required: true
expert_brief: null
device_actions: []
real_device_authorized: false
---


依据用户修订对照排查当前短回合；actor/critic最新revision14已完成，无需重复更改。专家brief待只读审查后按七字段写入，三条命令及范围已冻结。