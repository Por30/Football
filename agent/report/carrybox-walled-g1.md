---
task_id: "carrybox-walled-g1"
language: "zh-CN"
axes: ["E", "P", "L", "D"]
risk_tier: "T2"
status: "PARTIAL"
changed_files: ["source/perceptual_ball/perceptual_ball/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/smoke_carrybox_walled.py", "scripts/rsl_rl/smoke_carrybox_walled.sh", "tests/test_carrybox_walled.py", "docs/carrybox/walled/README.md", "docs/carrybox/walled/test_receipts.json", "docs/carrybox/walled/test_receipts_initial.json", "docs/carrybox/walled/test_receipts_primitive_failure.json", "docs/carrybox/walled/primitive_cylinder_failure.log", "docs/carrybox/walled/mesh_cylinder_failure.log", "docs/carrybox/smoke.json", "projects/carrybox/README.md", "projects/README.md", "README.md"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "92f70112e537d24b924ce67a25ba6bc941f6e81f0943e1b23723badcdbb5cfe4", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "a1752ba8bf74d1ac27bda79cf2fb5f9637780494c8fad325b1093a3a17ec86be", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_carrybox_walled.sh", "result": "FAIL", "exit_code": 137, "executed": true, "receipt_sha256": "20b4d65f83caa4c9b078e5dddba8095ded41f03e7fd51031d05b37d3da214d98", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "bbbdcb8747cc56f5d642404f89a89748942613a19a49340aa69b526987487eb9", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_carrybox.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "bfc09a947a1188d8a2742c446ec54a1268d07f1a789313b0ac0a48d521c77931", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
task_contract_sha256: "43621242fae043bbdd65c9c294ff2c06c0502a32efb9feab8bd22dadf3d7e29b"
artifact: "REPORT"
---

实现已接入，但GPU集成验收未完成，不能宣称可正式训练。wall3继承G1基线，wall4继承wall3；48×27配对深度扰动、无特权actor/critic、9维辅助标签、640维AMP、80/15/5参考初始化、运动学墙柱、yaw进程锚点课程、search奖励、非终止一次成功奖励，以及变体checkpoint校验/显式warm-start均已实现。源码和命令索引见docs/carrybox/walled/README.md。

CPU14项PASS，原CarryBox-v0真实4环境两次PPO/AMP更新、timeout、checkpoint、JIT/ONNX回归PASS。wall3在所有RSI组、墙柱碰撞schema、实际渲染变化检查后完成一次PPO更新，然后第二轮rollout发生PhysX GPU convexCoreConvexNphase_Kernel / CUDA700并挂起。第一次范围内修复解决原数据float64与测试固定PPO配置；第二次将原生圆柱改为网格凸包，仍重现相同GPU故障。根据skill两次修复边界停止修改；冻结RTX测试FAIL，进程被人工结束后返回137，不能把137当成正常退出。wall4真实测试因前一变体失败尚未运行。

没有正式训练、成功率评估或修改原始动作；足球PID2056902在最终只读检查仍运行，未操作它。清理了本次挂起的测试子进程，以及此前完成视频录制后仍挂起的自有录制进程；未删除输出。

迁移差异已明确：未得到X2父源码，继承本地G1奖励；相机扰动幅度为本地假设；参考缺少boxquat和平台几何，pickup/carry保持直立yaw代理，姿态课程仅loco；无putDown。resume按新进程重启yaw课程；默认wall播放含RSI，需数据集，部署actor则不需要。

使用说明与项目看板标为待验收/阻塞，不会把代码实现或单轮更新写成任务成功。
