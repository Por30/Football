---
task_id: "agilekickball-s2s-parity-20261015"
language: "zh-CN"
axes: ["E", "P", "C"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "你看一下球的质量和深度管线是否和训练一致 s2s表现比较差"
allowed_paths: ["scripts/sim2sim", "tests/test_kickball_parity.py", "docs/agilekickball_v4/sim2sim_parity_20261015", "projects/football/README.md", "projects/README.md", "agent"]
forbidden_scope: ["修改训练/共享G1资产/权重", "大规模GPU仿真或训练", "真实设备", "无证据调参或声称稳定迁移"]
development_modes: ["SIMULATOR_EXTENSION", "ML_DATA_PIPELINE"]
steps: ["核对训练快照、导出和MuJoCo实际编译参数", "专家只读审查质量/接触/深度接口", "同姿态训练函数逐像素重放和几何审计", "修复可确认的小范围不一致并执行数值及闭环检查", "记录差异、证据、限制与下一步"]
tests: [{"command": "/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_mujoco.py -v"}, {"command": "/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_parity.py -v"}, {"command": "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/audit_kickball_parity.py --output docs/agilekickball_v4/sim2sim_parity_20261015/audit.json"}]
stop_conditions: ["指定检查两次局部修复仍失败", "所加载策略与训练快照不匹配"]
safeguards: ["米制与相机外参/顺序/历史保持v4", "独立实际训练函数CPU对比；不把同一公式自测视作训练一致性", "读取MuJoCo编译后质量/惯性/阻尼/接触值", "未标定的PhysX/MuJoCo接触差异只报告，不直接猜测换算", "仅CPU短测，保留用户改动和训练进程", "do not tune guessed restitution mapping", "no GPU training or hardware", "preserve official robot model; report its known differences"]
expert_required: true
expert_brief: {"affected_call_path": ["v4 params/env.yaml -> perception.synthetic_ball_depth_image -> export -> kickball_mujoco.observe", "ball spawn/contact/serve -> MuJoCo make_scene"], "critical_interfaces": ["training snapshot, exported manifest, camera frame/history/units, ball mass/contact"], "invariants": ["no privileged actor inputs", "unchanged checkpoint and training", "same body pose for image comparison"], "smallest_change_locus": ["scripts/sim2sim/kickball_mujoco.py"], "mandatory_safeguards": ["do not tune guessed restitution mapping", "no GPU training or hardware", "preserve official robot model; report its known differences"], "minimal_tests": ["/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_mujoco.py -v", "/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_parity.py -v", "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/audit_kickball_parity.py --output docs/agilekickball_v4/sim2sim_parity_20261015/audit.json"], "blockers": []}
device_actions: []
real_device_authorized: false
---

T2 E/P/C审计；一个只读专家，主Agent负责最小实现与记录。

工件校验补正：专家最小测试描述绑定为原已冻结的三条逐字命令，英文安全条目原样并入既有同义安全边界；执行命令、范围及验收断言均未改变。
