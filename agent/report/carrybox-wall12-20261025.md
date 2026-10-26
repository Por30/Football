---
task_id: "carrybox-wall12-20261025"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall12-20261025.md", "agent/plan/carrybox-wall12-20261025.md", "agent/report/carrybox-wall12-20261025.md", "agent/task/carrybox-wall12-20261025.md", "docs/carrybox/wall12_20261025/README.md", "docs/carrybox/wall12_20261025/after_state.json", "docs/carrybox/wall12_20261025/artifact_validation.json", "docs/carrybox/wall12_20261025/attempt1/cpu.log", "docs/carrybox/wall12_20261025/attempt1/receipts.json", "docs/carrybox/wall12_20261025/attempt1/smoke.log", "docs/carrybox/wall12_20261025/attempt1/smoke_model.pt", "docs/carrybox/wall12_20261025/before/__init__.py", "docs/carrybox/wall12_20261025/before/carrybox_wall10.py", "docs/carrybox/wall12_20261025/before/play.py", "docs/carrybox/wall12_20261025/before/train.py", "docs/carrybox/wall12_20261025/before_state.json", "docs/carrybox/wall12_20261025/cpu.log", "docs/carrybox/wall12_20261025/exported/manifest.json", "docs/carrybox/wall12_20261025/exported/policy.onnx", "docs/carrybox/wall12_20261025/exported/policy.pt", "docs/carrybox/wall12_20261025/incompatible_auxiliary.pt", "docs/carrybox/wall12_20261025/incompatible_variant.pt", "docs/carrybox/wall12_20261025/receipts.json", "docs/carrybox/wall12_20261025/smoke.json", "docs/carrybox/wall12_20261025/smoke.log", "docs/carrybox/wall12_20261025/smoke.py", "docs/carrybox/wall12_20261025/smoke_model.pt", "docs/carrybox/wall12_20261025/source_identity.json", "docs/carrybox/wall12_20261025/validate_cpu.sh", "docs/carrybox/wall12_20261025/validate_sim.sh", "projects/README.md", "projects/findbox/README.md", "scripts/rsl_rl/play.py", "scripts/rsl_rl/play_carrybox_walled.sh", "scripts/rsl_rl/train.py", "scripts/rsl_rl/train_carrybox_walled.sh", "source/perceptual_ball/perceptual_ball/carrybox_wall12.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall12.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall12_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall12.py", "tests/test_carrybox_wall12.py"]
task_contract_sha256: "720e88795198e21659f4b15af6943d95f15b10c5704e258ac053c6ac21fb6477"
tests: [{"command": "bash docs/carrybox/wall12_20261025/validate_cpu.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "9f4408325d3c6acf3fb926ad3848c03854cef0e288d3098d2a14d987eb94cfbe", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall12_20261025/validate_sim.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "08223b5f5ed75d72e2a6046561bb6b7d22850cd0ec458519e1394ce800925767", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

wall12独立实现完成：继承wall11，新增128→128→9深度位姿辅助头，coef1.0，12维相机系标签含实际尺寸作旋转对称判定；标签与带噪深度同capture，当前latent复用，pose head解冻并加入原Adam policy组，CNN与pose head实际更新。actor558＋4×27×48、critic123、AMP600、物理/奖励/24步/5×4保持。

44项CPU与16环境24步2＋1轮更新/保存严格恢复/终止配对/导出通过；位置/旋转loss有限，每轮仍20次CNN合批前向，联合Adam40→60次，pose动量精确恢复。真实wall11 model19999及辅助契约篡改被拒绝；旧wall11学习器权重加载保持。JIT/ONNX仅本体与深度输入，无pose/critic参数。

第一次仿真失败源于测试要求Adam步数标量恢复前后设备相同；map_location会迁移标量。修正为步数精确数值比较，动量仍精确同设备比较，失败日志与回执保留attempt1/；冻结两条命令随后均PASS。

复用工作区先前已有wall10辅助hook，其文件SHA保持；本次不修改该共享模块或足球任务，train/play与注册仅追加wall12分派。工程基线包含其他任务未提交修改，后续整理提交时须保留共享hook依赖与双方入口。详见docs/carrybox/wall12_20261025/README.md和source_identity.json。

未启动wall12正式训练，未迁移正式权重、未操作其他进程，未测4096耗时或收敛/位姿精度。正式启动命令：CARRYBOX_VARIANT=12 bash scripts/rsl_rl/train_carrybox_walled.sh --run_name wall12_depth_pose_aux；执行前按项目约定核对实时GPU资源。
