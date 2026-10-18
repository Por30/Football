---
task_id: "agilekickball-v5-no-randomization-20261017"
language: "zh-CN"
axes: ["C", "P"]
risk_tier: "T1"
status: "DONE"
changed_files: ["README.md", "agent/handoff/agilekickball-v5-no-randomization-20261017.md", "agent/plan/agilekickball-v5-no-randomization-20261017.md", "agent/report/agilekickball-v5-no-randomization-20261017.md", "agent/task/agilekickball-v5-no-randomization-20261017.md", "docs/agilekickball_v5/README.md", "docs/agilekickball_v5/no_randomization_20261017/README.md", "docs/agilekickball_v5/no_randomization_20261017/receipts.json", "docs/agilekickball_v5/randomization/README.md", "projects/README.md", "projects/football/README.md", "scripts/rsl_rl/smoke_agilekickball_v5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v5_env_cfg.py"]
task_contract_sha256: "f47469fee4c6520ad2466e34bb081e9399aef9497c5127e93a886fd90a01ee51"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p 'test_agilekickball_v5*.py' -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "724c177f9bc70f49b1633ce9690c70d45d8305d4b8faa944fe7528161b315529", "stdout_sha256": "9ea65d9c27827305dcb28fe9e3a7d27601d29a048236bccaa56091e3fdfd4dce", "stderr_sha256": "9961046cb5af5081d1544d2f0014316e9e0f351b6ee9733aa4ad58299216a647", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

默认关闭v5的Kp/Kd随机化和全部深度噪声，复用现有倍率1及clean-depth分支。保留场景自遮挡、奖励、AMP、网络和训练配方。仅两处生产默认值改动；历史随机化GPU smoke显式True以保留其验收语义，没有执行该GPU脚本。

冻结CPU套件PASS，未增加镜像配置测试。项目入口、总看板和说明已同步。旧带扰动checkpoint需要显式True/True才可精确恢复；新无扰动默认需新实验。本次未改checkpoint兼容检查或revision，未启动、停止或重启训练。

22:35 JST只读检查时原v5 PID3429618已退出，无train/play进程；这不构成训练完成或成功率证据。结果和命令见docs/agilekickball_v5/no_randomization_20261017/README.md，回执在同目录receipts.json。保留工作区所有既有CarryBox改动。
