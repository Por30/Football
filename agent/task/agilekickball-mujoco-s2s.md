---
task_id: "agilekickball-mujoco-s2s"
language: "zh-CN"
axes: ["E", "P", "C", "L", "S"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "先把本地仓库更新到最新的支支 然后继宁宁s2s"
allowed_paths: ["unitree_mujoco", "unitree_rl_lab", "perceptual_ball/scripts/sim2sim", "perceptual_ball/tests/test_kickball_mujoco.py", "perceptual_ball/docs/agilekickball_v4/sim2sim_20261014", "perceptual_ball/agent", "perceptual_ball/projects/football/README.md", "perceptual_ball/projects/README.md", "perceptual_ball/README.md"]
forbidden_scope: ["真机/DDS控制", "启动停止训练", "覆盖已有改动或训练模型", "改变训练和共享CNN/export"]
development_modes: ["BUILD_TOOLING", "MODEL_DEPLOYMENT", "SIMULATOR_EXTENSION", "CONTROL_LOOP"]
steps: ["备份并更新官方main", "编译G1与MuJoCo", "实现v4解析深度/本体/PD适配", "执行冻结CPU及闭环短测", "记录模型差异和实际迁移表现并更新入口"]
tests: [{"command": "bash scripts/sim2sim/check_unitree_build.sh"}, {"command": "/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_mujoco.py -v"}, {"command": "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --headless --duration 10 --output docs/agilekickball_v4/sim2sim_20261014/smoke.json"}]
safeguards: ["检查关节完整唯一、输入输出shape/finite、control_dt整数分频；PD每physics step更新，力矩遵守官方ctrlrange与actuatorfrcrange。", "JSON记录模型/策略hash、参数差异、控制步数、推理耗时、球可见帧、饱和及root<.4m跌倒次数；不隐藏reset或失败。", "CPU有界线程；不启动DDS、真机或训练，不影响现有GPU任务。"]
stop_conditions: ["关键模型/策略无法加载或映射无法在允许范围内确定。", "shape、finite、力矩边界失败或MuJoCo数值故障，经最多两次范围内修复仍失败。", "必须新增真机通信、训练、破坏已有改动或扩大范围才能继续。"]
expert_required: true
expert_brief: {"affected_call_path": ["v4最终policy.pt+manifest -> CPU MuJoCo observation/depth -> PD；官方控制器只编译。"], "critical_interfaces": ["flat1x864、depth1x8x27x48、29关节、50Hz；physics_dt .002；head site torso下(.0039635,0,-.044)。", "v4球面解析射线米制深度，无场景遮挡；所有本体scale为1。"], "invariants": ["term-major oldest-to-newest；reset重复首帧；last_action保存raw action。", "保留官方质量35.112kg及力矩边界，记录训练33.341kg及腰部frame差异。", "测试验证历史、映射、旋转、FK、解析深度、动作与各关节力矩上限。"], "smallest_change_locus": ["独立scripts/sim2sim、targeted test、足球文档；官方原始机器人XML与训练代码不改。"], "mandatory_safeguards": ["检查关节完整唯一、输入输出shape/finite、control_dt整数分频；PD每physics step更新，力矩遵守官方ctrlrange与actuatorfrcrange。", "JSON记录模型/策略hash、参数差异、控制步数、推理耗时、球可见帧、饱和及root<.4m跌倒次数；不隐藏reset或失败。", "CPU有界线程；不启动DDS、真机或训练，不影响现有GPU任务。"], "minimal_tests": ["bash scripts/sim2sim/check_unitree_build.sh", "/home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p test_kickball_mujoco.py -v", "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --headless --duration 10 --output docs/agilekickball_v4/sim2sim_20261014/smoke.json"], "blockers": ["关键模型/策略无法加载或映射无法在允许范围内确定。", "shape、finite、力矩边界失败或MuJoCo数值故障，经最多两次范围内修复仍失败。", "必须新增真机通信、训练、破坏已有改动或扩大范围才能继续。"]}
device_actions: []
real_device_authorized: false
---

使用唯一只读组合轴专家审查结果。用户授权更新与s2s，无额外审批。官方模型边界保持；允许跌倒reset继续完成接口smoke，但稳定迁移必须明确判为失败。
