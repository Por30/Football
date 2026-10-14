---
task_id: "carrybox-wall4-after-football"
language: "zh-CN"
axes: ["E", "L", "A"]
risk_tier: "T2"
status: "BLOCKED"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "scripts/rsl_rl/smoke_carrybox_walled.py", "scripts/rsl_rl/smoke_carrybox_walled.sh", "scripts/rsl_rl/queue_wall4.py", "tests/test_carrybox_queue.py", "projects/findbox/README.md", "projects/football/README.md", "projects/README.md", "docs/carrybox/wall4_queue/README.md", "docs/carrybox/wall4_queue/blocking_wall3_pass.log", "docs/carrybox/wall4_queue/blocking_wall4_failure.log", "docs/carrybox/wall4_queue/cpu.log", "docs/carrybox/wall4_queue/pose_only_failure.log", "docs/carrybox/wall4_queue/test_receipts.json", "docs/carrybox/wall4_queue/walled3/smoke.log", "docs/carrybox/wall4_queue/walled3/smoke_model.pt", "docs/carrybox/wall4_queue/walled3/train/events.out.tfevents.1791897517.cao.2277501.0", "docs/carrybox/wall4_queue/walled3/train/events.out.tfevents.1791897634.cao.2278133.0", "docs/carrybox/wall4_queue/walled3/train/events.out.tfevents.1791897895.cao.2279987.0", "docs/carrybox/wall4_queue/walled3/train/model_0.pt", "docs/carrybox/wall4_queue/walled3/train/model_2.pt", "docs/carrybox/wall4_queue/walled4/smoke.log", "docs/carrybox/wall4_queue/walled4/train/events.out.tfevents.1791897745.cao.2278835.0", "docs/carrybox/wall4_queue/walled4/train/model_0.pt", "logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/config.json", "logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/queue.lock", "logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/registration.json", "logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/status.json", "logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/supervisor.log"]
task_contract_sha256: "4ca12f8cf5357f822abf87147aa3d799bfb526b6c3d9506a9beba5c0d556d050"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "92f70112e537d24b924ce67a25ba6bc941f6e81f0943e1b23723badcdbb5cfe4", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "699645a91888e1757896508c352a6872e4d6a0401c90647d63a9dd3a10a94cb6", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_carrybox_walled.sh", "result": "FAIL", "exit_code": 137, "executed": true, "receipt_sha256": "20b4d65f83caa4c9b078e5dddba8095ded41f03e7fd51031d05b37d3da214d98", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "0c41b22fd6797fe64f44ebfe5cf82d2421940fee4d7241df73db51b451c1e15f", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python scripts/rsl_rl/queue_wall4.py --check-only", "result": "FAIL", "exit_code": 1, "executed": true, "receipt_sha256": "723dcc9082604a00fbdf372516fe2da14e2a65fbd939adb2fe862256bb07f7f6", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "9ee77c6ba380bf657bfac6243616209dfb3c0dae305382cc9f7d4b2b4e3788e0", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: "cat logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/status.json"
---

用户已授权football完成后启动wall4。后台等待器PID2280644已运行并确认WAITING_FOOTBALL心跳；足球PID2056902/start_ticks249758817仍正常运行，约46700/50000。未停止或重启足球，未启动正式wall4。队列已绑定足球身份/目标最终checkpoint/GPU UUID/源码及原始动作hash，但readiness为BLOCKED且smoke_evidence为空，所以足球完成后也不会绕过就绪检查启动。

修复walled运动学wall/platform/cylinder错误速度API，改为只写pose；相机改为直接在torso父坐标设置local安装扰动，转换OpenGL相机朝向，避免PhysX世界位姿与滞后的USD父世界位姿混用。移除由此不再需要的reset内sim.forward。walled migration_revision=2；actor/critic、AMP输入、奖励和football接口不变。

冻结检查：19项CPU合同PASS；GPU wall3短测在第一次PPO更新/保存后的下一rollout依然PhysX convexCoreConvexNphase/CUDA700，挂起后只终止本轮测试进程，回执exit137；queue --check-only因缺少有效smoke报告FAIL。128环境预检未执行。中间CUDA_LAUNCH_BLOCKING=1只让wall3通过，wall4失败，不能认为同步环境变量是可用解决方案。相机local偏移边界、三技能RSI及墙柱可见性断言在最终失败前通过，但不是整条训练验收。

原范围两次修复后仍失败，按工程skill停止试改。失败证据保存在docs/carrybox/wall4_queue，原walled迁移历史证据保留。当前状态是训练阻塞而非正式训练完成或策略评估完成；用户目标尚未完成。

下一步先只读查看队列status/registration和最新football日志，再建立定点GPU故障修复合同。现有用户训练授权持续有效，不需要重复申请；修复并获得真实PASS报告后，协调当前等待器并按新的源码/数据/报告hash重新登记。不要将空smoke_evidence手改成假的PASS，不要直接启动第二个等待器。队列拥有flock及launch-intent保护，自己启动的预检/训练遇错不自动重试。

待验证的正式配方为128环境、seed42、40000轮，从头初始化；正式输出logs/rsl_rl/g1_carrybox_depth/walled4/。修复后先做4环境实际runner三轮，再于football确认完成和GPU释放后做128环境有界预检，随后一次性启动长训。当前等待器源码包含该路径，但因当前就绪失败不会执行。
