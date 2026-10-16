---
task_id: "agilekickball-s2s-scene-depth-20261016"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["scripts/sim2sim/kickball_mujoco.py", "scripts/sim2sim/scene_depth.py", "scripts/sim2sim/depth_visualization.py", "scripts/sim2sim/audit_kickball_parity.py", "scripts/sim2sim/diagnose_kickball_speed.py", "source/perceptual_ball/perceptual_ball/kickball_depth.py", "tests/test_kickball_scene_depth.py", "tests/test_kickball_parity.py", "tests/test_kickball_ball_speed.py", "README.md", "projects/README.md", "projects/football/README.md", "docs/agilekickball_v4/sim2sim_20261014/README.md", "docs/agilekickball_v5/sim2sim_scene_20261016/README.md", "docs/agilekickball_v5/sim2sim_scene_20261016/attempt1_receipts.json", "docs/agilekickball_v5/sim2sim_scene_20261016/attempt1_tests.log", "docs/agilekickball_v5/sim2sim_scene_20261016/depth/depth.mp4", "docs/agilekickball_v5/sim2sim_scene_20261016/depth/depth_info.json", "docs/agilekickball_v5/sim2sim_scene_20261016/depth/depth_preview.png", "docs/agilekickball_v5/sim2sim_scene_20261016/depth/depth_raw.npz", "docs/agilekickball_v5/sim2sim_scene_20261016/expert_review.json", "docs/agilekickball_v5/sim2sim_scene_20261016/make_occlusion_preview.py", "docs/agilekickball_v5/sim2sim_scene_20261016/occlusion_preview.png", "docs/agilekickball_v5/sim2sim_scene_20261016/occlusion_samples.json", "docs/agilekickball_v5/sim2sim_scene_20261016/occlusion_samples.npz", "docs/agilekickball_v5/sim2sim_scene_20261016/receipts.json", "docs/agilekickball_v5/sim2sim_scene_20261016/review_notes.json", "docs/agilekickball_v5/sim2sim_scene_20261016/smoke.json", "docs/agilekickball_v5/sim2sim_scene_20261016/smoke.xml", "docs/agilekickball_v5/sim2sim_scene_20261016/source_hashes.json", "docs/agilekickball_v5/sim2sim_scene_20261016/validation_summary.json", "agent/plan/agilekickball-s2s-scene-depth-20261016.md", "agent/task/agilekickball-s2s-scene-depth-20261016.md", "agent/report/agilekickball-s2s-scene-depth-20261016.md", "agent/handoff/agilekickball-s2s-scene-depth-20261016.md"]
task_contract_sha256: "4cf730eccc88ace68d679e80acc561ac876856fed650c7cac5ad16d21576cac3"
tests: [{"command": "env LIBGL_ALWAYS_SOFTWARE=1 /home/cao/ENTER/envs/umr/bin/python -m unittest discover -s tests -p 'test_kickball*.py' -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "54088826cc775f5337a85d7f626376715997030251596ebd06be9583245a6206", "stdout_sha256": "61c157763c568adc93eb1acae012db877ffa515ff0020d9fd672aaace087c01c", "stderr_sha256": "114f0345c6c61f13b66bc62998a2bec4a05b1e0b8eb112ec89915ecc875dc857", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/umr/bin/python scripts/sim2sim/kickball_mujoco.py --headless --duration 2 --physics-dt 0.005 --depth-output docs/agilekickball_v5/sim2sim_scene_20261016/depth --output docs/agilekickball_v5/sim2sim_scene_20261016/smoke.json", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "ba6127773b99906f7d43767c58517a6f46d3fd5807e4a4dbc95116da60a5c0fe", "stdout_sha256": "b55156759e1e3eee183e03230c3b3e1f5cb5b44d4abb6b3163eb42eeb3feadc1", "stderr_sha256": "8d6176a440c8ba0460a3441c55619a5360c9b151b8711572da2f27b563101920", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

# 场景深度稳定状态

本次范围已完成。默认scene，相机为v5 world约定+X光轴；历史每20ms推进8帧，采集按profile周期保持。解析旧模式显式--depth-mode analytic。v5源深度契约严格验证；v4权重scene模式记录输入分布变化。28项检查及100步/20帧闭环通过，源hash、冻结回执、失败记录、遮挡预览在docs/agilekickball_v5/sim2sim_scene_20261016。

启动：`/home/cao/ENTER/envs/umr/bin/python /home/cao/perceptual_ball/scripts/sim2sim/kickball_mujoco.py --duration 60 --physics-dt 0.005 --speed 2 --output /home/cao/perceptual_ball/docs/agilekickball_v5/sim2sim_scene_20261016/viewer_run.json`。可指定--camera-profile；对v5必须与完整部署导出的profile匹配。原验证export缺少关节/action元数据，测试通过不意味着该目录可直接运行。

后续实际设备标定、场景视觉策略训练及独立任务评估是不同工作；不能从此次实现/短测推出实机或稳定迁移。保留共享工作区原有CarryBox修改与既有run.json，未启动/停止训练或真实设备。当前正式v4训练输入没有被改成场景深度，v5既有训练管线已经包含完整机身/地面。
