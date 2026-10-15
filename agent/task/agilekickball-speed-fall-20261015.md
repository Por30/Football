---
task_id: "agilekickball-speed-fall-20261015"
language: "zh-CN"
axes: ["C", "E", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "当前球速快的候候易易摔倒 分析是2么原因造成得"
allowed_paths: ["scripts/sim2sim/diagnose_kickball_speed.py", "docs/agilekickball_v4/speed_fall_20261015", "projects/football/README.md", "projects/README.md", "agent"]
forbidden_scope: ["修改生产s2s/共享资产/策略/训练", "正式评估或GPU训练", "真机控制"]
development_modes: ["CONTROL_LOOP", "SIMULATOR_EXTENSION"]
steps: ["核对当前模型、训练速度课程和用户操作方式", "专家只读审查事件与最小对照", "固定场景扫描1/2/3/4/6m/s并记录失稳前后状态", "选复现跌倒速度做无球碰撞/固定站姿等局部对照", "汇总原因证据、限制和下一步并校验工件"]
tests: [{"command": "/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_mujoco.py -v"}, {"command": "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/diagnose_kickball_speed.py --output docs/agilekickball_v4/speed_fall_20261015/results.json"}]
stop_conditions: ["数值非有限或MuJoCo warning", "两次局部修复后指定检查仍失败"]
safeguards: ["只读生产配置和checkpoint；诊断场景修改只在独立进程内", "使用当前修正深度，固定步长0.005、球位置及策略", "分开接触前失稳、接触后跌倒与回合恢复；不把接触步数当成功率", "无碰撞等反事实仅作诊断，不作为部署配置", "单场景结果不当成总体失败率或唯一根因", "仅CPU短仿真，不启动训练或真实设备"]
expert_required: true
expert_brief: {"affected_call_path": ["checkpoint curriculum -> policy", "KickballSim.observe/target/torque -> mj_step -> recovery"], "critical_interfaces": ["ball speed and collision, torque limits, recovery gate"], "invariants": ["same checkpoint and start state", "chronological event timestamps"], "smallest_change_locus": ["standalone diagnostic script"], "mandatory_safeguards": ["只读生产配置和checkpoint；诊断场景修改只在独立进程内", "使用当前修正深度，固定步长0.005、球位置及策略", "分开接触前失稳、接触后跌倒与回合恢复；不把接触步数当成功率", "无碰撞等反事实仅作诊断，不作为部署配置", "单场景结果不当成总体失败率或唯一根因", "仅CPU短仿真，不启动训练或真实设备"], "minimal_tests": ["/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_mujoco.py -v", "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/diagnose_kickball_speed.py --output docs/agilekickball_v4/speed_fall_20261015/results.json"], "blockers": []}
device_actions: []
real_device_authorized: false
---

T2局部工程诊断；每个速度最长20秒，反事实最长20秒，允许按首个跌倒提前终止并完整保存轨迹。
