---
task_id: "AGILE-V3-STATE-FEEDBACK-20261006"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/state_feedback.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/export.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_outcome_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3_outcome.py", "tests/test_state_feedback.py", "tests/test_agilekickball_v3.py", "tests/test_agilekickball_v3_outcome.py", "tests/test_contact_outcome.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "scripts/rsl_rl/train_agilekickball_v3.sh", "docs/agilekickball_v3/README.md", "docs/agilekickball_v3/state_feedback_20261006", "README.md", "agent/plan/agilekickball-v3-state-feedback.md", "agent/task/agilekickball-v3-state-feedback.md", "agent/report/agilekickball-v3-state-feedback.md", "agent/handoff/agilekickball-v3-state-feedback.md", "logs/rsl_rl/agilekickball_v3/2026-10-06_13-17-10_state_feedback_20261006_scratch", "logs/background/agilekickball_v3_state_feedback_20261006_131706.log", "logs/background/agilekickball_v3_state_feedback_20261006_131706.pid", "logs/rsl_rl/agilekickball_v3_smoke/2026-10-06_13-16-16_state_feedback_scale_smoke"]
task_contract_sha256: "b56f1a916a4ddc9a2e2ec2b44965a0021f24b8c34b0f81179faea4e6174cda2f"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_state_feedback.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "8a64957c8c0dbaa892b025807418a3d94725b313191624ba19ab65e0dc9d6912", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "0c74eb2ba93ebe433dfd497906a96e44fda6259f40fb64f0ed7b74a4a2af7fc3", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "2c2cdedcfd922b65a901ff9fbcdfea89ab151033175e669e47945355a8beed98", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "23ac37891e89e2679e54253d760b2ea090dbd42d62eb4c2d0c8f832ed62d11d4", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v3.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "1d62a83bc8ed2afddb0ddf08e9ab2de07b15492cd74d08f81223147e2124831e", "stdout_sha256": "f22a7d05dbb944e86d062c5b2823ee16c52ffbdf0cede9cffd4720bd326051b0", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

实现、冻结验证和用户授权的后台正式训练启动均已完成。进程 1499582，session 同 PID，详情及 start_ticks 在 docs/agilekickball_v3/state_feedback_20261006/launch.json；首先核对 PID 启动时间，禁止重复启动或终止训练。当前新 revision state_feedback_20261006，从零初始化。原 Outcome 与 v2 checkpoint 不能用新任务 resume。

入口 scripts/rsl_rl/train_agilekickball_v3.sh；算法 rsl_rl_extensions/state_feedback.py；v3 物理状态继承 v2。观测仍为 proprio_hist/perception，预测头 current root-frame position + world velocity rotated by full root orientation，尺度 [3,3,3,6,6,6]。完整 actor 包含状态头/门控/修正，export 已同步；任何辅助回退必须一起恢复 encoder、head 和深拷贝 Adam，禁止只训练头绕过 KL。

三个冻结命令最终全部 PASS；两次 smoke 测试接口修复及旧 receipts 保留。正式启动核验第 11 轮（0 起）正常，first checkpoint 有限且模块在更新。尚未完成长训或性能评测；不要用这一工程 DONE 声称比 v2 更好。关注 Loss/state_feedback/total_aux_updates、residual_abs_mean_raw、gate_mean、Loss/aux/skipped_batches、stage_monitor_kl，以及课程进度、恢复比例和分组球状态误差。

状态查看命令：tail -n 100 /home/cao/perceptual_ball/logs/background/agilekickball_v3_state_feedback_20261006_131706.log
进程查看命令：ps -p 1499582 -o pid,sid,etime,args
模型目录：/home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v3/2026-10-06_13-17-10_state_feedback_20261006_scratch
运行源文件快照/哈希：docs/agilekickball_v3/state_feedback_20261006/source_snapshot_manifest.json。

新几何与 v2 一致（2 m、±0.25 m、0.6 m），最高球速 6 m/s 只是课程终点。旧更宽任务通过 Template-Perceptual-Ball-AgileKickball-v3-Outcome 加载；旧模型已在仿真 smoke 中用归档类读取验证。若随后需要恢复中断的新训练，必须显式指定当前 run/checkpoint 并保持新方法配置；不要把该命令当作当前待办，本轮已启动且无需恢复。
