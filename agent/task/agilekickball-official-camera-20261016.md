---
task_id: "agilekickball-official-camera-20261016"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["SIMULATOR_EXTENSION", "MODEL_DEPLOYMENT"]
original_request: "根据官方g1给的文档保持一致"
allowed_paths: ["docs/agilekickball_v5/official_g1_camera_20261016", "docs/agilekickball_v5/camera_unitree_g1_d435i.json", "docs/agilekickball_v5/sim2sim_scene_20261016/README.md", "scripts/sim2sim/scene_depth.py", "scripts/sim2sim/kickball_mujoco.py", "source/perceptual_ball/perceptual_ball/kickball_depth.py", "tests/test_kickball_scene_depth.py", "README.md", "projects/football/README.md", "projects/README.md", "agent/plan/agilekickball-official-camera-20261016.md", "agent/task/agilekickball-official-camera-20261016.md", "agent/report/agilekickball-official-camera-20261016.md", "agent/handoff/agilekickball-official-camera-20261016.md"]
forbidden_scope: ["正式训练或checkpoint修改", "共享机器人资产/执行器/物理步长修改", "CarryBox修改", "真实硬件操作"]
steps: ["保存官方G1模型与相机例程证据，核对安装和采集参数", "按D435i官方640x480 Z16 60fps新增独立profile并保留旧契约", "实现60Hz相机在物理tick采集及50Hz策略取最新帧，记录量化延迟和丢帧", "验证官方配置/异步时序/旧profile契约及现有场景遮挡", "运行冻结检查和短闭环，保存回执、更新文档和工程交接"]
tests: [{"command": "env LIBGL_ALWAYS_SOFTWARE=1 /home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p 'test_kickball*.py' -v"}, {"command": "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --headless --duration 2 --physics-dt 0.005 --depth-output docs/agilekickball_v5/official_g1_camera_20261016/depth --output docs/agilekickball_v5/official_g1_camera_20261016/smoke.json"}, {"command": "/home/cao/ENTER/envs/umr/bin/python docs/agilekickball_v5/official_g1_camera_20261016/audit_official_camera.py"}]
stop_conditions: ["需要扩大allowed_paths", "需要真实设备或正式训练", "冻结检查两次局部修复后仍失败"]
safeguards: ["保持50Hz控制、固定物理步长、动作/力矩边界与机身/环境遮挡", "只把官方例程640x480/60fps称为示例配置，不冒充所有出厂流模式", "URDF安装来源锁定rev_1_0；光学内参官方要求设备读取，名义值不标实测", "相机按绝对相位在physics tick采集，记录实际/计划时刻；不把policy采样50Hz冒称60Hz", "保留既有v5 checkpoint profile与严格契约；新subpolicy采集仅显式支持的s2s路径使用", "不启动训练、不切换现有checkpoint、不修改共享机器人资产", "官方示例/图示参数与名义K/主点/单位假设、项目分辨率/裁剪/历史分开记录，保持nominal_unverified", "URDF安装不是已标定深度光心外参", "采集按t0+n*period绝对相位，禁止上次实际采集时间加period漂移", "采集用第一个不早于计划的physics tick，实际/计划/量化延迟记录，正常延迟不超过physics_dt", "拒绝physics_dt>采集周期；跳时记录缺失帧，不补造或改时间戳", "分开实际采集数、policy消费数、覆盖未消费帧与漏采帧", "policy仅用实际时间<=当前的最新帧并记录帧龄；重复observe不额外采集；reset重设相位而serve保持", "非policy物理tick用积分后几何；验证mj_kinematics与同状态mj_forward射线深度一致", "明确2秒端点是否计入60Hz采集统计", "旧20msprofile/严格契约/v4分布标记/遮挡/物理不变回归保持"]
expert_required: true
expert_brief: {"affected_call_path": ["独立官方profile → select_profile → physics tick绝对相位采集 → policy50Hz取最新帧", "mj_step后到期时更新几何采集；官方来源审计"], "critical_interfaces": ["D435i官方例程640x480 Z16 60fps；get_intrinsics设备读取", "官方图VFOV55.2度、光轴对竖直42.4度；rev1_0 URDF安装", "allow_subpolicy_capture默认False，仅s2s显式True", "640x480完整nearest-exact缩放48x27，fx/fy和主点同步变换"], "invariants": ["固定physics_dt、50Hz控制、动作/力矩与完整遮挡保持", "旧camera_nominal/v5checkpoint契约和analytic保持", "v5优先源profile且覆盖不一致拒绝", "光轴米制float32，历史20ms滚动"], "smallest_change_locus": ["新增官方profile和证据", "kickball_depth验证能力参数", "scene_depth绝对相位缓存日志", "kickball_mujoco物理tick采集和统计；原场景测试补充"], "mandatory_safeguards": ["官方示例/图示参数与名义K/主点/单位假设、项目分辨率/裁剪/历史分开记录，保持nominal_unverified", "URDF安装不是已标定深度光心外参", "采集按t0+n*period绝对相位，禁止上次实际采集时间加period漂移", "采集用第一个不早于计划的physics tick，实际/计划/量化延迟记录，正常延迟不超过physics_dt", "拒绝physics_dt>采集周期；跳时记录缺失帧，不补造或改时间戳", "分开实际采集数、policy消费数、覆盖未消费帧与漏采帧", "policy仅用实际时间<=当前的最新帧并记录帧龄；重复observe不额外采集；reset重设相位而serve保持", "非policy物理tick用积分后几何；验证mj_kinematics与同状态mj_forward射线深度一致", "明确2秒端点是否计入60Hz采集统计", "旧20msprofile/严格契约/v4分布标记/遮挡/物理不变回归保持"], "minimal_tests": ["env LIBGL_ALWAYS_SOFTWARE=1 /home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p 'test_kickball*.py' -v", "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --headless --duration 2 --physics-dt 0.005 --depth-output docs/agilekickball_v5/official_g1_camera_20261016/depth --output docs/agilekickball_v5/official_g1_camera_20261016/smoke.json", "/home/cao/ENTER/envs/umr/bin/python docs/agilekickball_v5/official_g1_camera_20261016/audit_official_camera.py"], "blockers": []}
device_actions: []
real_device_authorized: false
---

# 工程范围

只调整足球s2s相机配置与采集时序；旧v5训练profile/模型契约保留。先冻结组合轴专家brief，再实现并执行原样测试。
