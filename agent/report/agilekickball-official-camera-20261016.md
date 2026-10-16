---
task_id: "agilekickball-official-camera-20261016"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["docs/agilekickball_v5/camera_unitree_g1_d435i.json", "scripts/sim2sim/scene_depth.py", "scripts/sim2sim/kickball_mujoco.py", "source/perceptual_ball/perceptual_ball/kickball_depth.py", "tests/test_kickball_scene_depth.py", "README.md", "projects/README.md", "projects/football/README.md", "docs/agilekickball_v5/sim2sim_scene_20261016/README.md", "docs/agilekickball_v5/official_g1_camera_20261016/README.md", "docs/agilekickball_v5/official_g1_camera_20261016/audit.json", "docs/agilekickball_v5/official_g1_camera_20261016/audit_official_camera.py", "docs/agilekickball_v5/official_g1_camera_20261016/depth/depth.mp4", "docs/agilekickball_v5/official_g1_camera_20261016/depth/depth_info.json", "docs/agilekickball_v5/official_g1_camera_20261016/depth/depth_preview.png", "docs/agilekickball_v5/official_g1_camera_20261016/depth/depth_raw.npz", "docs/agilekickball_v5/official_g1_camera_20261016/expert_review.json", "docs/agilekickball_v5/official_g1_camera_20261016/official_sources.json", "docs/agilekickball_v5/official_g1_camera_20261016/receipts.json", "docs/agilekickball_v5/official_g1_camera_20261016/review_notes.json", "docs/agilekickball_v5/official_g1_camera_20261016/smoke.json", "docs/agilekickball_v5/official_g1_camera_20261016/smoke.xml", "docs/agilekickball_v5/official_g1_camera_20261016/source_hashes.json", "docs/agilekickball_v5/official_g1_camera_20261016/unitree_d435i_fov.png", "agent/plan/agilekickball-official-camera-20261016.md", "agent/task/agilekickball-official-camera-20261016.md", "agent/report/agilekickball-official-camera-20261016.md", "agent/handoff/agilekickball-official-camera-20261016.md"]
task_contract_sha256: "ddc516a59513d585a7910ba2e7fe2a834c679ad518d323313c9559da8d8aa430"
tests: [{"command": "env LIBGL_ALWAYS_SOFTWARE=1 /home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p 'test_kickball*.py' -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "54088826cc775f5337a85d7f626376715997030251596ebd06be9583245a6206", "stdout_sha256": "9789a6d7183996f65aeecb45519794127133a28d516800bd976a7bdfca7f89ff", "stderr_sha256": "b630e9aed64b772755f40f35e97c5a6bae667922bd9f5bb9782937f95f368527", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --headless --duration 2 --physics-dt 0.005 --depth-output docs/agilekickball_v5/official_g1_camera_20261016/depth --output docs/agilekickball_v5/official_g1_camera_20261016/smoke.json", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "f71b9b5c20ca45144b8cd2c435a819faeb42d8833edae580ac14f7ccfcd2ae4a", "stdout_sha256": "52375d24f5d583c5c7885cc8c6616ae40461786f96f6965bb7925b601c79ad53", "stderr_sha256": "8d6176a440c8ba0460a3441c55619a5360c9b151b8711572da2f27b563101920", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/umr/bin/python docs/agilekickball_v5/official_g1_camera_20261016/audit_official_camera.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "02ec8bfb657b7226559a1836b46cb2d4fb688ef7ff25cca7a5c860815eb721ec", "stdout_sha256": "3162da1bb67b2a7b709365cd0b4dc35372878148207b9802707d44a61f144e57", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

# 官方G1相机对齐结果

已从宇树公开SPA目录与CDN读取官方Depth Camera Routine和About G1，确认D435i、示例深度640x480 Z16 60fps；官方图VFOV55.2度、光轴相对竖直42.4度。安装位置/47.6度下俯与锁定commit的官方G1 rev_1_0 URDF一致。新独立默认profile保存上述参数及名义K/单位/项目参数来源。

s2s相机按t0+n/60在固定物理tick采集，策略50Hz取最新帧；积分后mj_kinematics更新几何，未改physics_dt、控制/力矩边界。采集计划/实际时刻、帧龄、覆盖/漏采分别记录。source K由官方垂直视场和方形像素/中心主点假设推导，单位0.001也是名义值；官方要求逐台get_intrinsics，保持nominal_unverified，不声称光心外参已实测。

三条冻结命令全部PASS：31项检查（含实际GUI、原遮挡/契约和新增异步/动态几何/漏采测试）、2秒真实策略闭环与20帧视频、独立官方事实和时序审计。5ms物理步长下121次采集含0/2秒端点，100次policy消费100个不同帧、20未消费覆盖、1末帧待消费；漏采0，最大量化延迟3.333ms，最大帧龄10ms，无数值故障/跌倒。短测不证明接球稳定。

原camera_nominal.json hash不变，v5已有导出优先源profile，默认训练验证仍拒绝未实现物理tick采集的60Hz profile。未改变旧v5训练、模型checkpoint、机器人资产或任何真实设备。新profile当前用于s2s；当前默认v4权重继续标记输入分布变化。
