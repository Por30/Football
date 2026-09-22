---
task_id: "ENG-G1-SOCCER-V3-20260919"
status: "DONE"
language: "zh-CN"
axes: ["E", "P", "C", "L", "D", "S"]
risk_tier: "T2"
changed_files: ["source/perceptual_ball/perceptual_ball/amp_features.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/amp.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/algorithm.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/modules.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/export.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/perceptual_ball_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/soccer_env.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/soccer_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agents/rsl_rl_ppo_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/amp.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/events.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_state.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/soccer_v3.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/depth_v3.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/smoke_soccer_v3.py", "scripts/rsl_rl/smoke_soccer_v3.sh", "scripts/rsl_rl/train_soccer_v3.sh", "tests/test_soccer_v3.py", "docs/research/iros2027/SOCCER_V3.md", "docs/research/iros2027/v3_test_receipts.json", "docs/research/iros2027/v3_artifact_validation.json", "docs/research/iros2027/validation/smoke_model.pt", "docs/research/iros2027/validation/smoke_v3.log", "docs/research/iros2027/validation/smoke_v3.json", "docs/research/iros2027/validation/exported/manifest.json", "docs/research/iros2027/validation/exported/policy.onnx", "docs/research/iros2027/validation/exported/policy.pt", "agent/plan/g1-soccer-v3.md", "agent/task/g1-soccer-v3.md", "agent/report/g1-soccer-v3.md", "agent/handoff/g1-soccer-v3.md"]
task_contract_sha256: "acd5267f781def68fd1dd8407476dcb345a8dd2578d691ea6dca11fdebff27b9"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_soccer_v3.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "f98b3af5225002c9dd389df5ac57b81c02d4b856396f68badf45b7ba77926690", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "a5dadddf7c0febaea6683fb845c678d4e172fcf93b2c6f1f0dfce5345b6aba9d", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_soccer_v3.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "e5018c6b950808f9f13d89dc5e7827c003bc2eff50c0878a7f724fda5f087353", "stdout_sha256": "2415a7848c8cc96e66d273c28ea355bad3225cc03cae74a1682feb2cc85fd5d9", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

# G1 Soccer v3 工程结果

已修复审查中确认的 AMP 特征、terminal/timeout、checkpoint、接触门控、CNN 导出及偏置问题，并注册独立任务 Template-Perceptual-Ball-Soccer-v3。新增定向回球、连续站稳恢复、发球分母/失败分类、带延迟/丢帧的合成深度，以及融合本体感知的辅助回归。默认低速训练，关闭推力并减小 COM 扰动。

两条冻结命令均 PASS：10 项 CPU 正确性回归；真实 IsaacLab CPU、2 环境的接触与训练 smoke。左右动作的参考末端 FK 最大误差分别 6.11e-7/7.04e-7 m，低于预设 3 mm 容差。最终真实接触峰值 4.25 N，两次脚触球进入 RECOVER；PPO 一次更新、AMP/辅助分支、checkpoint roundtrip 和完整导出正常。CPU 测试另核对 JIT/ONNX 与原始网络在 batch 1/4 下的一致性。

集成时发现通配 Robot/.* 过滤形状合法但无力数据，已改为显式 28 个碰撞部件并在 smoke 校验 USD 集合。测试摆球需避开实际膝下碰撞几何；调整的是测试条件，未放宽成功/非脚碰球断言。验证过程中保留失败诊断，最终绑定回执对应修复后的命令。

启动说明在 docs/research/iros2027/SOCCER_V3.md。新增启动脚本完成 bash 语法与 --help 入口检查。未启动长期 GPU 训练、未进行实机测试或策略性能评估；未修改旧参考动作/旧 checkpoint。深度遮挡是球体代理；默认来球 0.4–0.8 m/s；训练状态恢复不含仿真瞬时状态、课程计数和 CUDA RNG，不能宣称逐步精确复现。
