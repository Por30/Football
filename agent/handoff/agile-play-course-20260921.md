---
task_id: "ENG-AGILE-PLAY-COURSE-20260921"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "HANDOFF"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/audit_agilekickball.py", "tests/test_agile_play_course.py", "docs/agilekickball/training_audit_20260921/training_course_samples.pt", "docs/agilekickball/training_audit_20260921/receipts.json", "docs/agilekickball/training_audit_20260921/replay.log", "docs/agilekickball/training_audit_20260921/default_play_course_samples.pt", "docs/agilekickball/training_audit_20260921/README.md", "docs/agilekickball/training_audit_20260921/play_fix_receipts.json", "docs/agilekickball/training_audit_20260921/replay.json", "docs/agilekickball/training_audit_20260921/near_incoming.json", "docs/agilekickball/training_audit_20260921/tensorboard_summary.json", "agent/plan/agile-play-course-20260921.md", "agent/task/agile-play-course-20260921.md", "agent/report/agile-play-course-20260921.md", "agent/handoff/agile-play-course-20260921.md"]
task_contract_sha256: "6a97741d2621cb23a9cf9a97f265ee4b5a804e5a2188061263e5e7c9f24c82bc"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agile_play_course.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "3cd2b1b8597ce96faf516aead2bb1fc92889098f693cc8c019b1e6ec9aedfc6d", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "cdd45671c523b4f61c957572a903998481884f5ff505ba373d977f4cddd5db22", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/audit_agilekickball.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "fd874a4d4a218bf5dda994ff634b17acf02e64cca0f2b9267a46d1367ac4d418", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
resume_command: null
---

完成播放课程恢复的局部修复：load_optimizer=False仍恢复checkpoint曝光计数，play加载后reset一次使首球使用恢复范围。未改训练、奖励、网络或checkpoint，无优化器更新。CPU证明优化器load不被调用、load不瞬移球、explicit reset采用恢复距离；真实生产runner加载证明课程和首球1.3–2m范围、policy输出不变。可直接重放已有model_25200，无需重训。

详细指标、口径、原始证据及播放命令见docs/agilekickball/training_audit_20260921/README.md。速度标量与向量误差分开，不将代理次数写成成功率。关键近脚盲区尚未修复，CPU无梯度回放不代表真机或全部checkpoint。
