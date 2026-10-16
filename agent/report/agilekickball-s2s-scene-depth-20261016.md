---
task_id: "agilekickball-s2s-scene-depth-20261016"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["scripts/sim2sim/kickball_mujoco.py", "scripts/sim2sim/scene_depth.py", "scripts/sim2sim/depth_visualization.py", "scripts/sim2sim/audit_kickball_parity.py", "scripts/sim2sim/diagnose_kickball_speed.py", "source/perceptual_ball/perceptual_ball/kickball_depth.py", "tests/test_kickball_scene_depth.py", "tests/test_kickball_parity.py", "tests/test_kickball_ball_speed.py", "README.md", "projects/README.md", "projects/football/README.md", "docs/agilekickball_v4/sim2sim_20261014/README.md", "docs/agilekickball_v5/sim2sim_scene_20261016/README.md", "docs/agilekickball_v5/sim2sim_scene_20261016/attempt1_receipts.json", "docs/agilekickball_v5/sim2sim_scene_20261016/attempt1_tests.log", "docs/agilekickball_v5/sim2sim_scene_20261016/depth/depth.mp4", "docs/agilekickball_v5/sim2sim_scene_20261016/depth/depth_info.json", "docs/agilekickball_v5/sim2sim_scene_20261016/depth/depth_preview.png", "docs/agilekickball_v5/sim2sim_scene_20261016/depth/depth_raw.npz", "docs/agilekickball_v5/sim2sim_scene_20261016/expert_review.json", "docs/agilekickball_v5/sim2sim_scene_20261016/make_occlusion_preview.py", "docs/agilekickball_v5/sim2sim_scene_20261016/occlusion_preview.png", "docs/agilekickball_v5/sim2sim_scene_20261016/occlusion_samples.json", "docs/agilekickball_v5/sim2sim_scene_20261016/occlusion_samples.npz", "docs/agilekickball_v5/sim2sim_scene_20261016/receipts.json", "docs/agilekickball_v5/sim2sim_scene_20261016/review_notes.json", "docs/agilekickball_v5/sim2sim_scene_20261016/smoke.json", "docs/agilekickball_v5/sim2sim_scene_20261016/smoke.xml", "docs/agilekickball_v5/sim2sim_scene_20261016/source_hashes.json", "docs/agilekickball_v5/sim2sim_scene_20261016/validation_summary.json", "agent/plan/agilekickball-s2s-scene-depth-20261016.md", "agent/task/agilekickball-s2s-scene-depth-20261016.md", "agent/report/agilekickball-s2s-scene-depth-20261016.md", "agent/handoff/agilekickball-s2s-scene-depth-20261016.md"]
task_contract_sha256: "4cf730eccc88ace68d679e80acc561ac876856fed650c7cac5ad16d21576cac3"
tests: [{"command": "env LIBGL_ALWAYS_SOFTWARE=1 /home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p 'test_kickball*.py' -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "54088826cc775f5337a85d7f626376715997030251596ebd06be9583245a6206", "stdout_sha256": "61c157763c568adc93eb1acae012db877ffa515ff0020d9fd672aaace087c01c", "stderr_sha256": "114f0345c6c61f13b66bc62998a2bec4a05b1e0b8eb112ec89915ecc875dc857", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --headless --duration 2 --physics-dt 0.005 --depth-output docs/agilekickball_v5/sim2sim_scene_20261016/depth --output docs/agilekickball_v5/sim2sim_scene_20261016/smoke.json", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "ba6127773b99906f7d43767c58517a6f46d3fd5807e4a4dbc95116da60a5c0fe", "stdout_sha256": "b55156759e1e3eee183e03230c3b3e1f5cb5b44d4abb6b3163eb42eeb3feadc1", "stderr_sha256": "8d6176a440c8ba0460a3441c55619a5360c9b151b8711572da2f27b563101920", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

# 场景深度实现结果

s2s默认scene改用完整可见机身网格、地面、球和模型中其他静动态物体的最近表面，输出光轴Z米制；复用v5相机profile/部署预处理验证，保持50Hz历史与控制。独立感知model只修改geom分组，不改变live动力学；源v5契约逐字段检查，v4权重分布变化明确记录。旧审计/诊断显式analytic保留。

冻结28项检查（包含实际GUI、近远/离轴/动态姿态/遮挡/契约/历史/物理不变）及2秒100步真实TorchScript+MuJoCo闭环全部PASS，20帧视频已解码核验。新增环境contact mask/绝对meshdir保留检查通过。实际G1抬臂161机身像素后移动隐藏球，深度差为零；新增墙体245像素遮挡球，图/NPZ/数值均保存。

初次单位测试把float32的1500×0.001要求严格等于1.5而失败；生产运算未改，已知样本改为可精确表示的1250→1.25，严格断言保留，初次失败回执与日志保留。最终28项全部通过。

v5接入用真实验证权重与契约、同G1任务部署元数据合成临时manifest；原验证目录缺少部署元数据，不能直接启动。相机仍nominal_unverified；v4旧权重尚未适应新分布，100步接口通过不代表接球稳定。MuJoCo几何与训练USD仍有差异。未启动正式训练、修改checkpoint或操作真实硬件。用户提供实际CameraInfo/光学外参/采集时序后可继续核对实机一致性。
