---
task_id: "agilekickball-s2s-scene-depth-20261016"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["SIMULATOR_EXTENSION", "MODEL_DEPLOYMENT"]
original_request: "要和实机相同 把机身的遮挡和地面等等其他环境都考虑到深度图"
allowed_paths: ["scripts/sim2sim/kickball_mujoco.py", "scripts/sim2sim/scene_depth.py", "scripts/sim2sim/depth_visualization.py", "scripts/sim2sim/audit_kickball_parity.py", "scripts/sim2sim/diagnose_kickball_speed.py", "tests/test_kickball_scene_depth.py", "tests/test_kickball_parity.py", "source/perceptual_ball/perceptual_ball/kickball_depth.py", "docs/agilekickball_v5/sim2sim_scene_20261016", "docs/agilekickball_v4/sim2sim_20261014/README.md", "projects/football/README.md", "projects/README.md", "README.md", "agent/plan/agilekickball-s2s-scene-depth-20261016.md", "agent/task/agilekickball-s2s-scene-depth-20261016.md", "agent/report/agilekickball-s2s-scene-depth-20261016.md", "agent/handoff/agilekickball-s2s-scene-depth-20261016.md", "tests/test_kickball_ball_speed.py"]
forbidden_scope: ["正式训练与checkpoint修改", "共享G1模型/动力学/力矩边界修改", "CarryBox代码与数据修改", "真实硬件或DDS控制"]
steps: ["审查v5相机/导出契约并接收组合轴专家建议", "实现场景可见表面求交及相机profile/历史时序", "接入s2s默认场景模式与显式legacy兼容并更新可视化标签", "验证机身/地面/任意障碍遮挡、近远平面、动态姿态与契约拒绝", "执行冻结CPU及短闭环命令，保存深度证据和工程记录"]
tests: [{"command": "env LIBGL_ALWAYS_SOFTWARE=1 /home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p 'test_kickball*.py' -v"}, {"command": "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --headless --duration 2 --physics-dt 0.005 --depth-output docs/agilekickball_v5/sim2sim_scene_20261016/depth --output docs/agilekickball_v5/sim2sim_scene_20261016/smoke.json"}]
stop_conditions: ["需要扩大allowed_paths", "需要启动正式训练或真实硬件", "冻结检查两次局部修复后仍失败"]
safeguards: ["保留50Hz控制、本体顺序、29关节映射、动作/力矩/finite边界和恢复逻辑", "复用v5 profile验证与光轴米制、不加入球真值策略输入", "场景包括完整机身可见网格、地面和静动态物体，排除重复碰撞代理", "v4输入分布变化明确记录；v5 profile/深度契约不匹配拒绝", "不因相机近裁剪面前的表面遮蔽有效远处几何", "保持旧审计/诊断显式analytic重放", "cutoff覆盖far/min(ray_forward)，最终按光轴Z裁剪", "首交点Z<near从near平面重投，保留闭合物体near后的出口", "包含静态几何且不排除torso；仅排机器人重复碰撞代理，不排环境表面", "感知模型仅改geom分组；capture读取mj_forward后最新位姿，验证索引", "profile采集周期为20ms整数倍，期间保持上一帧；history每policy tick滚动；reset清缓存重复首帧；保存采集时序", "v5默认使用导出profile；覆盖不一致/缺失profile/契约字段错误/选择analytic均拒绝", "v4 scene允许诊断但启动和结果标明分布变化；历史审计显式analytic", "scene有效深度不称球可见性；窗口/视频/JSON语义一致", "GUI测试输出临时目录并使用可用显示与软件渲染", "验证离轴Z、near后表面、隐藏球遮挡、静动态物体、姿态、时序/reset、契约拒绝与物理不变", "名义profile未标定，记录MuJoCo实际几何/后端，不声称实机一致或Warp数值等同"]
expert_required: true
expert_brief: {"affected_call_path": ["run → KickballSim契约 → observe → 场景深度 → History → policy", "reset/serve → mj_forward → live几何位姿", "窗口/视频读取同一策略深度；历史审计显式analytic"], "critical_interfaces": ["v5 world约定+X光轴/+Y左/+Z上，torso link相对wxyz外参，target_intrinsics整数像素中心", "float32[27,48]光轴米制0.1–3；[1,8,27,48]旧到新；不归一化", "独立感知model与live data的geom/mesh/BVH/位姿索引相同", "严格验证完整v5源契约和profile，MuJoCo运行后端单独记录"], "invariants": ["50Hz控制、本体顺序、29关节、动作/力矩/finite/恢复保持", "不向策略额外输入球真值或分割/可见性", "v4解析数值及非单位四元数重放保留", "不修改live动力学模型", "完整可见机身、球、地面及静动态场景求最近表面"], "smallest_change_locus": ["scene_depth.py局部封装", "kickball_mujoco.py接入与契约/时序", "depth_visualization.py按实际模式标记", "历史审计显式analytic；新增场景测试"], "mandatory_safeguards": ["cutoff覆盖far/min(ray_forward)，最终按光轴Z裁剪", "首交点Z<near从near平面重投，保留闭合物体near后的出口", "包含静态几何且不排除torso；仅排机器人重复碰撞代理，不排环境表面", "感知模型仅改geom分组；capture读取mj_forward后最新位姿，验证索引", "profile采集周期为20ms整数倍，期间保持上一帧；history每policy tick滚动；reset清缓存重复首帧；保存采集时序", "v5默认使用导出profile；覆盖不一致/缺失profile/契约字段错误/选择analytic均拒绝", "v4 scene允许诊断但启动和结果标明分布变化；历史审计显式analytic", "scene有效深度不称球可见性；窗口/视频/JSON语义一致", "GUI测试输出临时目录并使用可用显示与软件渲染", "验证离轴Z、near后表面、隐藏球遮挡、静动态物体、姿态、时序/reset、契约拒绝与物理不变", "名义profile未标定，记录MuJoCo实际几何/后端，不声称实机一致或Warp数值等同"], "minimal_tests": ["env LIBGL_ALWAYS_SOFTWARE=1 /home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p 'test_kickball*.py' -v", "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --headless --duration 2 --physics-dt 0.005 --depth-output docs/agilekickball_v5/sim2sim_scene_20261016/depth --output docs/agilekickball_v5/sim2sim_scene_20261016/smoke.json"], "blockers": []}
device_actions: []
real_device_authorized: false
---

# 执行范围

单一组合轴专家只读审查；主Agent实施。默认场景深度支持实际可见几何遮挡，名义profile不声明实机标定完成。以下命令覆盖已有回归和2秒CPU真实策略闭环，验证产物写入独立docs目录。
