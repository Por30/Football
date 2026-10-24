---
task_id: "carrybox-wall10-perf-20261023"
language: "zh-CN"
axes: ["L", "P"]
risk_tier: "T2"
status: "DONE"
changed_files: ["docs/carrybox/wall10_20261023/README.md", "docs/carrybox/wall10_perf_20261023/README.md", "docs/carrybox/wall10_perf_20261023/benchmark_learning.py", "docs/carrybox/wall10_perf_20261023/benchmark_sim.py", "docs/carrybox/wall10_perf_20261023/finalize_records.py", "docs/carrybox/wall10_perf_20261023/run_sim.sh", "docs/carrybox/wall10_perf_20261023/smoke.py", "docs/carrybox/wall10_perf_20261023/validate_cpu.sh", "docs/carrybox/wall10_perf_20261023/validate_learning.sh", "docs/carrybox/wall10_perf_20261023/validate_sim.sh", "projects/README.md", "projects/findbox/README.md", "source/perceptual_ball/perceptual_ball/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall10.py", "tests/test_carrybox_wall10_perf.py"]
task_contract_sha256: "4cb4b2d4b62563d66a96712602440cd6faadeda936c3d89e83485ac824e6f329"
tests: [{"command": "bash docs/carrybox/wall10_perf_20261023/validate_cpu.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "87171151780f4988ebab1850f9c82129a96d27a0fa93fc07ec64c031cd48d4fe", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall10_perf_20261023/validate_learning.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "a1440e8c75dbe78605c4d46c2f7aa107a0e1b9c691b3426ad3503893836c56d2", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall10_perf_20261023/validate_sim.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "c8c759d59e39905039f472c6e62c4aee68fb91ff9c896008d502f42a91475de1", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

4096×100完整短测从52.81s降到18.49s/轮，学习从40.89s降到7.63s；另测4096×24为4.41s/轮。

仅改变wall10计算布局、箱体深度kernel和零外力写入；原训练与任务参数保持，默认100步。34项CPU、16环境更新/恢复/导出、4096完整短测通过。旧正式checkpoint可严格恢复；未启动正式训练，不声称学习收敛或GPU逐位等价。

稳定代码及计时、浮点差异和首次验证脚本修复记录见docs/carrybox/wall10_perf_20261023/README.md。复核使用Task中三条冻结命令，均为docs内验证，不触发正式训练。
