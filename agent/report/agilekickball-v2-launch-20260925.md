---
task_id: "AGILE-V2-LAUNCH-20260925"
language: "zh-CN"
axes: ["A"]
risk_tier: "T1"
status: "DONE"
changed_files: ["agent/handoff/agilekickball-v2-launch-20260925.md", "agent/plan/agilekickball-v2-launch-20260925.md", "agent/report/agilekickball-v2-launch-20260925.md", "agent/task/agilekickball-v2-launch-20260925.md", "docs/agilekickball_v2/launch_20260925/artifacts.json", "docs/agilekickball_v2/launch_20260925/launch.json", "docs/agilekickball_v2/launch_20260925/receipts.json", "docs/agilekickball_v2/launch_20260925/verified_start.json", "docs/agilekickball_v2/launch_20260925/verify_start.py"]
task_contract_sha256: "5d188aa9908536342e09f5fbe00ce89b104428f1a7c8d42f67b40c5b2091f281"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/agilekickball_v2/launch_20260925/verify_start.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "201269e96968beab1fa32a77692b6042bb5f2d06384075b76b81a80603277c41", "stdout_sha256": "419d9b2993a13344bbff6610a86309962208d488e52dfd7225a7b4a7acd5623e", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

用户授权的新版v2从零后台训练已启动，PID 9824，独立session，父进程退出后仍运行。4096环境、cuda:0、50000轮、seed42、resume=false。未修改源代码。

验证到第12轮；实际模型0的control_steps=24、schema5、revision=v1_speed_only_20260925，尚未解锁扩展；保存agent/env参数与请求一致，reward有限且TensorBoard已有标量。显存约15770MiB，迭代约2.44秒。完成的是启动和检查，训练尚在持续，不表示50000轮训练完成或技能已收敛。

训练目录：`/home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v2/2026-09-25_22-18-55_v1_speed_only_20260925_scratch`。

stdout：`/home/cao/perceptual_ball/logs/background/agilekickball_v2_20260925_221850.log`。

查看命令：`tail -f /home/cao/perceptual_ball/logs/background/agilekickball_v2_20260925_221850.log`。

TensorBoard：`tensorboard --logdir /home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v2/2026-09-25_22-18-55_v1_speed_only_20260925_scratch`。

后续先读本启动记录及进程状态，不重复启动；未要求修改配置、停止任务或自动调参。源码与设计见上一轮speed_only_20260925记录。
