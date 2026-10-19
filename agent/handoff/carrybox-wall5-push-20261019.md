---
task_id: "carrybox-wall5-push-20261019"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "tests/test_carrybox_push.py", "docs/carrybox/wall5_push_20261019", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-push-20261019.md", "agent/task/carrybox-wall5-push-20261019.md", "agent/report/carrybox-wall5-push-20261019.md", "agent/handoff/carrybox-wall5-push-20261019.md"]
task_contract_sha256: "b9bd89c2a8ad26291434f7d7cfef7132f190a89b562d5e0c91f7a109a261485b"
tests: [{"command": "bash docs/carrybox/wall5_push_20261019/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "8b926d7c8d674370c5862be3b9a44f6debb5b6c9b60c0893921b77fe0bfdf1c7", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_push_20261019/replay.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "e2d0bab91f9ba2bdb231879742d57a0c18698d09af4eaeabde039f95ee551719", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_push_20261019/smoke.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "a29b9c7de10fb14c83c32cdcf3058820aa960b38499fb2741f7884c7ffde3050", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

稳定状态：wall5源码revision15；后台正式PID4038923仍执行已加载的revision14，2026-10-19 12:08:52 JST快照10779轮。所有旧数据/日志/checkpoint和用户既有未提交修改保留。不得把源码新配置称为已在当前训练生效。

唯一生产差异在两份wall5文件，before副本位于docs/carrybox/wall5_push_20261019/before。新契约显式记录增量推扰和地面/default材料；旧完整resume被拒绝，不能绕过严格加载。当前训练不需要动作；未来启动时先核对进程/GPU，用户此次没有要求重启。

三个固定检查命令及真实receipt见frontmatter。诊断脚本及验证模型均留docs，不属于正式训练。复跑GPU验证前核对至少4GiB空闲；此前并发诊断短时抬高正式轮时，退出后恢复约4秒。

工程实现和验证完成，尚未证明学习改善。下一项建议单独诊断loco前20步pitch、策略动作/PD目标、脚接触与参考姿态；三组均在首次push前约13步倾倒，不能只用push解释。继续保持用户RSI80/0/20和非对称AC，除非新任务明确改变。详见同目录README和replay_summary.json的完成/删失分母。
