---
task_id: "agilekickball-v5-randomization"
language: "zh-CN"
axes: ["C", "P", "A"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/kickball_randomization.py", "source/perceptual_ball/perceptual_ball/kickball_randomized_camera.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v5.py", "tests/test_agilekickball_v5_randomization.py", "scripts/rsl_rl/smoke_agilekickball_v5.py", "scripts/rsl_rl/smoke_agilekickball_v5.sh", "scripts/rsl_rl/smoke_agilekickball_v5_randomization.sh", "docs/agilekickball_v5/README.md", "docs/agilekickball_v5/randomization", "README.md", "projects/README.md", "projects/football/README.md", "agent"]
artifact: "TASK"
status: "FROZEN"
original_request: "同时给v5 加上一些kpkd和深度信息的噪声随机化 便于部署"
development_modes: ["SIMULATOR_EXTENSION", "ML_TRAINING"]
forbidden_scope: ["改v4/Wall4/共享资产或动作奖励", "启动正式训练或真实设备", "随机化范围冒充实机标定"]
steps: ["核对gain与sensor接口并冻结范围", "实现每回合增益和每帧深度随机化、版本合同", "CPU及4环境几何/增益/噪声/PPO恢复导出验证", "记录参数与限制、更新入口看板"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v5*.py -v"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v5_randomization.sh"}]
safeguards: ["仅v5配置与专属sensor；保留v4/Wall4和既有运行进程", "增益从default重采而非累乘，同时同步PhysX/data/actuator", "每新采集帧仅加噪一次；partial reset只更新所选env，miss保持far", "真实光学profile与训练随机化分离，不增加策略/critic特权输入", "噪声只在仿真训练应用，export不再次加噪；版本合同严格拒绝旧配置"]
stop_conditions: ["禁止只改PhysX而漏actuator增益", "禁止每次observation读取重新采样噪声", "冻结失败仅两次范围内修复，不放宽断言"]
expert_required: true
expert_brief: {"affected_call_path": ["v5 reset -> official gain randomizer -> implicit actuator/PhysX; Warp capture -> noise -> obs -> checkpoint/export"], "critical_interfaces": ["SensorBase capture caching/subset reset", "默认增益与actuator/PhysX同步"], "invariants": ["仅v5配置与专属sensor；保留v4/Wall4和既有运行进程", "增益从default重采而非累乘，同时同步PhysX/data/actuator", "每新采集帧仅加噪一次；partial reset只更新所选env，miss保持far", "真实光学profile与训练随机化分离，不增加策略/critic特权输入", "噪声只在仿真训练应用，export不再次加噪；版本合同严格拒绝旧配置"], "smallest_change_locus": ["v5 config/MDP；新增v5 tensor noise及camera子类"], "mandatory_safeguards": ["仅v5配置与专属sensor；保留v4/Wall4和既有运行进程", "增益从default重采而非累乘，同时同步PhysX/data/actuator", "每新采集帧仅加噪一次；partial reset只更新所选env，miss保持far", "真实光学profile与训练随机化分离，不增加策略/critic特权输入", "噪声只在仿真训练应用，export不再次加噪；版本合同严格拒绝旧配置"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v5*.py -v", "bash scripts/rsl_rl/smoke_agilekickball_v5_randomization.sh"], "blockers": ["禁止只改PhysX而漏actuator增益", "禁止每次observation读取重新采样噪声"]}
device_actions: []
real_device_authorized: false
---

为v5增加训练域随机化。唯一只读专家wall4_perf_review已核对ImplicitActuator、官方事件与capture生命周期；保留既有相机profile，将随机化合同另列。GPU只做4环境短测，不停Wall4、不启动正式训练，不声称已验证真机效果。
