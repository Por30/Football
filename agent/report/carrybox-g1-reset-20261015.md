---
task_id: "carrybox-g1-reset-20261015"
language: "zh-CN"
axes: ["E", "L", "C"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "tests/test_carrybox_g1_reset.py", "tests/test_carrybox_walled.py", "docs/carrybox/g1_reset_20261015", "logs/rsl_rl/g1_carrybox_depth/walled4", "README.md", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-g1-reset-20261015.md", "agent/task/carrybox-g1-reset-20261015.md", "agent/report/carrybox-g1-reset-20261015.md", "agent/handoff/carrybox-g1-reset-20261015.md"]
task_contract_sha256: "8dd9ae79685e5ca39a8748d7ce98192fa114c667b0d2bfce3bb74e631e5864a0"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "92f70112e537d24b924ce67a25ba6bc941f6e81f0943e1b23723badcdbb5cfe4", "stdout_sha256": "7ffec10452f4b4d1f4048b256d6c95a68b84dc92aa91d739f09ea48da6b38cfd", "stderr_sha256": "5a1e1b278e51b09caaae8e0a6438f045a7bfd010e991bb72641d67298096cd6e", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/g1_reset_20261015/validate.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "9ef76efded194db2f43374b3f39e4bb9b1a6f2f0620242b5e965be2c1092a13c", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

完成本轮站立reset诊断、G1适配修复、仿真验收及已授权的后台wall4正式启动；DONE表示本轮工程/启动完成，不表示正式40000轮训练结束或策略收敛。

旧model_14000在revision7环境中1600个loco完成回合全部第3步真实tipped，头高仍约1.15m；初始姿态正常，策略首步诱发大横滚角速度。保持RSI关节目标平均38.93步，清零初始化速度50.39步，默认站姿开环57.75步；这些对照不证明站立稳定。保留失败阈值及奖励，没有因该短测新增failure penalty。

另确认G1脚底初始化穿地最高17.74mm，公共wall MDP新增实际碰撞凸包支撑点缓存及每次RSI最低点补偿，root/参考箱/支撑台同步向上，保持速度/关节，部分reset不动其他环境。revision8、schema2，wall3/wall4共享修复且其余仅障碍和身份不同。源G1 D435安装和实际相机父变换一致，墙/柱/身体遮挡通过；未宣称实机光心标定完成。无特权观测、原始AMP和足球/共享资产未改。

44项CPU PASS；16环境三技能接地≥5mm、状态请求/读回、实际深度与目标、fresh首4步无普遍3步reset、PPO/AMP更新/恢复/导出通过；loco/pickup/hold均有完整AMP历史。4096×24步、4epochs×4minibatches：热身平均4.544秒，最慢4.664秒。正式启动前GPU只剩桌面12MiB；诊断进程全部清理。前期测试mock、隔离探针及USD碰撞父节点读取问题已修；失败及中断记录保留，CPU最终回执单独复查，GPU通过后仅修改旧CPU mock与增加断言，未改生产代码。

2026-10-15 13:06:49 JST启动PID2660033，4096环境、40000轮、seed42、fresh，无resume/warm_start；13:10:49核验到iteration12，model_0.pt为schema2/revision8/15段AMP且参数有限，正式热身均值4.238秒、最慢4.33秒。训练仍后台运行。完整路径、日志命令、测试回执和限制见docs/carrybox/g1_reset_20261015/README.md及formal_check.json。后续分别监控三技能，独立完整地面拾箱评估待做，不能将hold RSI成功作为完整流程成功。
