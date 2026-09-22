---
task_id: "ENG-PLAY-BALLSPEED-20260921"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "HANDOFF"
status: "DONE"
changed_files: ["scripts/rsl_rl/play.py", "scripts/rsl_rl/cli_args.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_state.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v1.py", "tests/test_play_ballspeed.py", "docs/agilekickball_v1/README.md", "docs/agilekickball_v1/play_ballspeed_receipts.json", "agent/plan/play-ballspeed.md", "agent/task/play-ballspeed.md", "agent/report/play-ballspeed.md", "agent/handoff/play-ballspeed.md"]
task_contract_sha256: "8c7f1a4285188b9020187324567baa12585ed135649cbfcd3b1b1d5aa4697f0e"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_play_ballspeed.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "706000957b18913f54c8db837ba8dd5bceada41f373d56fb7ec984b52ac133e8", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "d9e3175f4f1574345dc92cbe4f2800dde6dba95439b66a48e1f9dd57dc845be6", "runner": "run_engineering_tests.py"}]
resume_command: null
---

play新增可选--ballspeed MIN MAX（m/s）。argparse启动仿真前校验有限正数与顺序，支持相等上下界固定速度。checkpoint加载后设置运行时override并显式reset，基础采样helper每次优先使用override；v1绕过阶段混合，显式评估范围不标成挑战数据且课程冻结。未传参默认不变，不改训练配置或checkpoint。

13项CPU回归通过，包含原v1状态/播放加载、真实双参数解析、非法输入、固定值、v0曝光课程与重复reset覆盖、v1 stage9下低速覆盖及恢复重发。未另跑GUI仿真；共享原状态类用已有物理边界double测试。用法见docs/agilekickball_v1/README.md末节。
